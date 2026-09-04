from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response

from apps.api.src.auth import ActorContext, ActorRole, get_actor_context, require_role, require_verified_actor
from apps.api.src.config import use_in_memory_repositories
from apps.api.src.db.database import SessionLocal
from apps.api.src.deps import (
    get_account_repo,
    get_escalation_service,
    get_worker_relationship_repo,
    get_idempotency_service,
    get_shift_lifecycle_service,
    get_shift_repo,
    get_organisation_repo,
    get_shift_service,
)
from apps.api.src.helpers import _now_or, _shift_view
from apps.api.src.models.shift import Shift
from apps.api.src.rate_limit import actor_or_ip, limiter
from apps.api.src.repository_dependencies import get_request_unit_of_work
from apps.api.src.repositories.account_repository import AccountRepository
from apps.api.src.repositories.shift_repository import ShiftRepository
from apps.api.src.repositories.sqlalchemy_shift_repository import SqlAlchemyShiftRepository
from apps.api.src.routes.idempotency_support import IdempotencyKeyHeader, replayed
from apps.api.src.routes.service_errors import raise_service_error
from apps.api.src.schemas import ErrorResponse, ShiftCreateRequest, ShiftResponse
from apps.api.src.schemas_recovery import (
    CancellationRequest,
    ShiftAdvanceRequest,
    ShiftLifecycleRequest,
    ShiftUpdateRequest,
)
from apps.api.src.services.errors import ServiceError
from apps.api.src.services.geocoding import geocode
from apps.api.src.services.idempotency import IdempotencyConflict, IdempotencyService
from apps.api.src.repositories.worker_relationship_repository import WorkerRelationshipRepository
from apps.api.src.services.escalation_service import EscalationService
from apps.api.src.services.org_affiliation import sibling_employed_now
from apps.api.src.services.shift_visibility import worker_can_see_shift
from apps.api.src.services.shift_service import ShiftService
from apps.api.src.services.shift_lifecycle_service import ShiftLifecycleService
from apps.api.src.unit_of_work import RequestUnitOfWork

router = APIRouter(tags=["shifts"])

MAX_SHIFT_RANGE = timedelta(days=186)


@router.post("/shifts", response_model=ShiftResponse, responses={400: {"model": ErrorResponse}})
@limiter.limit("20/hour", key_func=actor_or_ip)
def create_shift(
    request: Request,
    payload: ShiftCreateRequest,
    response: Response,
    idempotency_key: IdempotencyKeyHeader = None,
    idempotency: IdempotencyService = Depends(get_idempotency_service),
    service: ShiftService = Depends(get_shift_service),
    shift_repo: ShiftRepository = Depends(get_shift_repo),
    actor: ActorContext = Depends(get_actor_context),
    account_repo: AccountRepository = Depends(get_account_repo),
    unit_of_work: RequestUnitOfWork = Depends(get_request_unit_of_work),
    escalations: EscalationService = Depends(get_escalation_service),
    relationship_repo: WorkerRelationshipRepository = Depends(get_worker_relationship_repo),
    organisation_repo=Depends(get_organisation_repo),
) -> ShiftResponse:
    require_role(actor.role, {ActorRole.OPERATOR})
    require_verified_actor(actor, "posting shifts")
    try:
        started = idempotency.start(actor.user_id, "shift.create", idempotency_key, payload.model_dump(mode="json"))
    except IdempotencyConflict as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    if started.cached_response is not None:
        return replayed(response, ShiftResponse, started.cached_response)
    currency = "GBP"
    if actor.account_id:
        account = account_repo.get(actor.account_id)
        if account:
            currency = account.currency
    if payload.rota_state == "draft" and (
        payload.assigned_worker_id is None or payload.workers_needed != 1
    ):
        raise HTTPException(
            status_code=400,
            detail="A draft rota shift needs exactly one assigned worker.",
        )
    if payload.assigned_worker_id is not None and actor.account_id:
        assignee = relationship_repo.get_for_venue_worker(actor.account_id, payload.assigned_worker_id)
        if assignee is None or assignee.status != "active":
            sibling = sibling_employed_now(
                organisation_repo, relationship_repo, actor.account_id, payload.assigned_worker_id
            )
            if sibling is None:
                raise HTTPException(
                    status_code=400,
                    detail="That worker does not have an active relationship with your venue.",
                )
    shift = service.create_shift(payload, actor.user_id, actor.account_id, currency)
    if payload.assigned_worker_id is not None:
        shift = replace(shift, assigned_worker_id=payload.assigned_worker_id)
    if payload.rota_state == "draft":
        shift = replace(shift, rota_state="draft")
    try:
        shift = shift_repo.save(escalations.stamp_new_shift(shift, shift.created_at))
    except ServiceError as exc:
        raise_service_error(exc)
    _schedule_geocode(unit_of_work, shift_repo, shift)
    result = _shift_view(shift)
    idempotency.finish(started.record_id, result.model_dump(mode="json"))
    return result


@router.post("/shifts/{shift_id}/advance", response_model=ShiftResponse, responses={400: {"model": ErrorResponse}, 404: {"model": ErrorResponse}})
def advance_shift(
    shift_id: str,
    payload: ShiftAdvanceRequest,
    actor: ActorContext = Depends(get_actor_context),
    escalations: EscalationService = Depends(get_escalation_service),
) -> ShiftResponse:
    require_role(actor.role, {ActorRole.OPERATOR})
    if not actor.account_id:
        raise HTTPException(status_code=403, detail="This account is not linked to a venue.")
    try:
        shift = escalations.advance_now(shift_id, actor.account_id, payload.target, _now_or(payload.now))
    except ServiceError as exc:
        raise_service_error(exc)
    return _shift_view(shift)


@router.get("/shifts", response_model=list[ShiftResponse])
def list_shifts(
    limit: int = Query(default=50, ge=1, le=100),
    role: str | None = None,
    location: str | None = None,
    starts_from: datetime | None = Query(default=None),
    starts_before: datetime | None = Query(default=None),
    service: ShiftService = Depends(get_shift_service),
    actor: ActorContext = Depends(get_actor_context),
    relationship_repo: WorkerRelationshipRepository = Depends(get_worker_relationship_repo),
) -> list[ShiftResponse]:
    require_role(actor.role, {ActorRole.OPERATOR, ActorRole.WORKER})
    if (starts_from is None) != (starts_before is None):
        raise HTTPException(status_code=400, detail="Provide both starts_from and starts_before, or neither.")
    if starts_from and starts_before and starts_before - starts_from > MAX_SHIFT_RANGE:
        raise HTTPException(status_code=400, detail="Shift ranges are limited to 186 days.")
    account_id = actor.account_id if actor.role == ActorRole.OPERATOR else None
    shifts = service.list_shifts(
        limit,
        role,
        location,
        account_id=account_id,
        starts_from=starts_from,
        starts_before=starts_before,
    )
    if actor.role == ActorRole.WORKER:
        worker_id = actor.effective_worker_id
        shifts = [
            item
            for item in shifts
            if item.status == "open" and worker_can_see_shift(item, worker_id, relationship_repo)
        ]
    return [_shift_view(item) for item in shifts]


@router.get("/shifts/{shift_id}", response_model=ShiftResponse, responses={404: {"model": ErrorResponse}})
def get_shift_by_id(
    shift_id: str,
    service: ShiftService = Depends(get_shift_service),
    actor: ActorContext = Depends(get_actor_context),
    relationship_repo: WorkerRelationshipRepository = Depends(get_worker_relationship_repo),
) -> ShiftResponse:
    try:
        shift = service.get_shift(shift_id)
        _require_shift_access(actor, shift)
        if actor.role == ActorRole.WORKER and not worker_can_see_shift(
            shift, actor.effective_worker_id, relationship_repo
        ):
            raise HTTPException(status_code=404, detail="Shift not found.")
        return _shift_view(shift)
    except ServiceError as exc:
        raise_service_error(exc)


@router.post("/shifts/{shift_id}/clone", response_model=ShiftResponse, responses={404: {"model": ErrorResponse}})
def clone_shift(
    shift_id: str,
    service: ShiftService = Depends(get_shift_service),
    actor: ActorContext = Depends(get_actor_context),
) -> ShiftResponse:
    try:
        shift = service.get_shift(shift_id)
        require_role(actor.role, {ActorRole.OPERATOR})
        if shift.account_id != actor.account_id:
            raise HTTPException(status_code=403, detail="Operator can only clone their own shifts.")
        return _shift_view(service.clone_shift(shift_id))
    except ServiceError as exc:
        raise_service_error(exc)


@router.put("/shifts/{shift_id}", response_model=ShiftResponse, responses={400: {"model": ErrorResponse}, 404: {"model": ErrorResponse}})
def update_shift(
    shift_id: str,
    request: ShiftUpdateRequest,
    service: ShiftLifecycleService = Depends(get_shift_lifecycle_service),
    shift_service: ShiftService = Depends(get_shift_service),
    shift_repo: ShiftRepository = Depends(get_shift_repo),
    actor: ActorContext = Depends(get_actor_context),
    unit_of_work: RequestUnitOfWork = Depends(get_request_unit_of_work),
) -> ShiftResponse:
    try:
        shift = shift_service.get_shift(shift_id)
        _require_shift_management(actor, shift)
        updated = service.update(shift_id, request)
        if updated.location != shift.location:
            _schedule_geocode(unit_of_work, shift_repo, updated)
        return _shift_view(updated)
    except ServiceError as exc:
        raise_service_error(exc)


@router.post("/shifts/{shift_id}/close", response_model=ShiftResponse, responses={400: {"model": ErrorResponse}, 404: {"model": ErrorResponse}})
def close_shift(
    shift_id: str,
    request: ShiftLifecycleRequest,
    service: ShiftLifecycleService = Depends(get_shift_lifecycle_service),
    shift_service: ShiftService = Depends(get_shift_service),
    actor: ActorContext = Depends(get_actor_context),
) -> ShiftResponse:
    try:
        _require_shift_management(actor, shift_service.get_shift(shift_id))
        return _shift_view(service.close(shift_id, request))
    except ServiceError as exc:
        raise_service_error(exc)


@router.post("/shifts/{shift_id}/cancel", response_model=ShiftResponse, responses={400: {"model": ErrorResponse}, 404: {"model": ErrorResponse}})
def cancel_shift(
    shift_id: str,
    request: CancellationRequest,
    service: ShiftLifecycleService = Depends(get_shift_lifecycle_service),
    shift_service: ShiftService = Depends(get_shift_service),
    actor: ActorContext = Depends(get_actor_context),
) -> ShiftResponse:
    try:
        _require_shift_management(actor, shift_service.get_shift(shift_id))
        return _shift_view(service.cancel(shift_id, request, actor.user_id))
    except ServiceError as exc:
        raise_service_error(exc)


def _schedule_geocode(unit_of_work: RequestUnitOfWork, shift_repo: ShiftRepository, shift: Shift) -> None:
    in_memory_repo = shift_repo if use_in_memory_repositories() else None
    unit_of_work.after_commit(lambda: _geocode_and_update(shift.shift_id, shift.location, in_memory_repo))


def _geocode_and_update(shift_id: str, location: str, in_memory_repo: ShiftRepository | None) -> None:
    lat, lng = geocode(location)
    if lat is None:
        return
    if in_memory_repo is not None:
        _store_coordinates(in_memory_repo, shift_id, lat, lng)
        return
    with SessionLocal() as session, session.begin():
        _store_coordinates(SqlAlchemyShiftRepository(session), shift_id, lat, lng)


def _store_coordinates(repo: ShiftRepository, shift_id: str, lat: float, lng: float) -> None:
    shift = repo.get(shift_id)
    if shift is not None:
        repo.save(replace(shift, latitude=lat, longitude=lng))


def _require_shift_access(actor: ActorContext, shift: Shift) -> None:
    require_role(actor.role, {ActorRole.OPERATOR, ActorRole.WORKER})
    if actor.role == ActorRole.OPERATOR and shift.account_id != actor.account_id:
        raise HTTPException(status_code=403, detail="Operator can only access their own shifts.")
    if actor.role == ActorRole.WORKER and shift.status != "open":
        raise HTTPException(status_code=403, detail="Worker can only access open shifts.")


def _require_shift_management(actor: ActorContext, shift: Shift) -> None:
    require_role(actor.role, {ActorRole.OPERATOR})
    if shift.account_id != actor.account_id:
        raise HTTPException(status_code=403, detail="Operator can only manage their active venue's shifts.")

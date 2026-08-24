from __future__ import annotations

from dataclasses import replace

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request, Response

from apps.api.src.auth import ActorContext, ActorRole, get_actor_context, require_role
from apps.api.src.config import get_bool_env, use_in_memory_repositories
from apps.api.src.db.database import SessionLocal
from apps.api.src.deps import (
    get_account_repo,
    get_idempotency_service,
    get_shift_lifecycle_service,
    get_shift_repo,
    get_shift_service,
    get_user_repo,
)
from apps.api.src.helpers import _shift_view
from apps.api.src.models.shift import Shift
from apps.api.src.rate_limit import actor_or_ip, limiter
from apps.api.src.repository_dependencies import get_request_unit_of_work
from apps.api.src.repositories.account_repository import AccountRepository
from apps.api.src.repositories.shift_repository import ShiftRepository
from apps.api.src.repositories.sqlalchemy_shift_repository import SqlAlchemyShiftRepository
from apps.api.src.repositories.user_repository import UserRepository
from apps.api.src.routes.service_errors import raise_service_error
from apps.api.src.schemas import ErrorResponse, ShiftCreateRequest, ShiftResponse
from apps.api.src.schemas_recovery import CancellationRequest, ShiftLifecycleRequest, ShiftUpdateRequest
from apps.api.src.services.errors import ServiceError
from apps.api.src.services.geocoding import geocode
from apps.api.src.services.idempotency import IdempotencyConflict, IdempotencyService
from apps.api.src.services.shift_service import ShiftService
from apps.api.src.services.shift_lifecycle_service import ShiftLifecycleService
from apps.api.src.unit_of_work import RequestUnitOfWork

router = APIRouter(tags=["shifts"])


def _geocode_and_update(
    shift_id: str,
    location: str,
    in_memory_repo: ShiftRepository | None = None,
) -> None:
    lat, lng = geocode(location)
    if lat is None:
        return
    if in_memory_repo is not None:
        shift = in_memory_repo.get(shift_id)
        if shift is not None:
            in_memory_repo.save(replace(shift, latitude=lat, longitude=lng))
        return
    session = SessionLocal()
    try:
        repo = SqlAlchemyShiftRepository(session)
        shift = repo.get(shift_id)
        if shift is not None:
            repo.save(replace(shift, latitude=lat, longitude=lng))
        session.commit()
    except BaseException:
        session.rollback()
        raise
    finally:
        session.close()


def _geocode_repo(repo: ShiftRepository) -> ShiftRepository | None:
    return repo if use_in_memory_repositories() else None


def _require_verified_operator(actor: ActorContext, user_repo: UserRepository) -> None:
    """Operators must verify their email before posting shifts.

    Skipped in DEV_MODE because header-based actors have no backing user record.
    Workers are intentionally not gated here — they may use the app while unverified.
    """
    if get_bool_env("DEV_MODE", False):
        return
    user = user_repo.get(actor.user_id)
    if user is None or not user.email_verified:
        raise HTTPException(
            status_code=403,
            detail="Verify your email before posting shifts. Check your inbox for the verification link.",
        )


@router.post("/shifts", response_model=ShiftResponse, responses={400: {"model": ErrorResponse}})
@limiter.limit("20/hour", key_func=actor_or_ip)
def create_shift(
    request: Request,
    payload: ShiftCreateRequest,
    response: Response,
    idempotency_key: str | None = Header(
        default=None,
        alias="Idempotency-Key",
        min_length=1,
        max_length=100,
        pattern="^[A-Za-z0-9._:-]+$",
    ),
    idempotency: IdempotencyService = Depends(get_idempotency_service),
    service: ShiftService = Depends(get_shift_service),
    shift_repo: ShiftRepository = Depends(get_shift_repo),
    actor: ActorContext = Depends(get_actor_context),
    account_repo: AccountRepository = Depends(get_account_repo),
    user_repo: UserRepository = Depends(get_user_repo),
    unit_of_work: RequestUnitOfWork = Depends(get_request_unit_of_work),
) -> ShiftResponse:
    require_role(actor.role, {ActorRole.OPERATOR})
    _require_verified_operator(actor, user_repo)
    try:
        started = idempotency.start(
            actor.user_id,
            "shift.create",
            idempotency_key,
            payload.model_dump(mode="json"),
        )
    except IdempotencyConflict as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    if started.cached_response is not None:
        response.headers["Idempotency-Replayed"] = "true"
        return ShiftResponse(**started.cached_response)
    currency = "GBP"
    if actor.account_id:
        account = account_repo.get(actor.account_id)
        if account:
            currency = account.currency
    shift = service.create_shift(payload, actor.user_id, actor.account_id, currency)
    geocode_repo = _geocode_repo(shift_repo)
    unit_of_work.after_commit(
        lambda: _geocode_and_update(shift.shift_id, shift.location, geocode_repo)
    )
    result = _shift_view(shift)
    idempotency.finish(started.record_id, result.model_dump(mode="json"))
    return result


@router.get("/shifts", response_model=list[ShiftResponse])
def list_shifts(
    limit: int = Query(default=50, ge=1, le=100),
    role: str | None = None,
    location: str | None = None,
    service: ShiftService = Depends(get_shift_service),
    actor: ActorContext = Depends(get_actor_context),
) -> list[ShiftResponse]:
    require_role(actor.role, {ActorRole.OPERATOR, ActorRole.WORKER})
    account_id = actor.account_id if actor.role == ActorRole.OPERATOR else None
    shifts = service.list_shifts(limit, role, location, account_id=account_id)
    if actor.role == ActorRole.WORKER:
        shifts = [item for item in shifts if item.status == "open"]
    return [_shift_view(item) for item in shifts]


@router.get("/shifts/{shift_id}", response_model=ShiftResponse, responses={404: {"model": ErrorResponse}})
def get_shift_by_id(
    shift_id: str,
    service: ShiftService = Depends(get_shift_service),
    actor: ActorContext = Depends(get_actor_context),
) -> ShiftResponse:
    try:
        shift = service.get_shift(shift_id)
        _require_shift_access(actor, shift)
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
            geocode_repo = _geocode_repo(shift_repo)
            unit_of_work.after_commit(
                lambda: _geocode_and_update(
                    updated.shift_id,
                    updated.location,
                    geocode_repo,
                )
            )
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

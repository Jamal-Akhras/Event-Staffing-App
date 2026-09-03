from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query

from apps.api.src.auth import ActorContext, ActorRole, get_actor_context, require_role
from apps.api.src.deps import get_event_recorder, get_shift_change_service
from apps.api.src.helpers import _now_or, _summary_view
from apps.api.src.models.shift_change_request import ShiftChangeRequest
from apps.api.src.repositories.organisation_repository import OrganisationRepository
from apps.api.src.repositories.shift_repository import ShiftRepository
from apps.api.src.repository_dependencies import get_organisation_repo, get_shift_repo
from apps.api.src.routes.service_errors import raise_service_error
from apps.api.src.schemas_shift_changes import (
    ShiftChangeAnswerRequest,
    ShiftChangeCreateRequest,
    ShiftChangeResponse,
)
from apps.api.src.services.errors import ServiceError
from apps.api.src.services.event_recorder import EventRecorder
from apps.api.src.services.shift_change_service import ShiftChangeService
from apps.api.src.services.shift_summary import summarise_shifts

router = APIRouter(tags=["shift changes"])


@router.post("/me/shift-change-requests", response_model=ShiftChangeResponse, status_code=201)
def create_change_request(
    payload: ShiftChangeCreateRequest,
    actor: ActorContext = Depends(get_actor_context),
    service: ShiftChangeService = Depends(get_shift_change_service),
    shifts: ShiftRepository = Depends(get_shift_repo),
    venues: OrganisationRepository = Depends(get_organisation_repo),
    recorder: EventRecorder = Depends(get_event_recorder),
) -> ShiftChangeResponse:
    require_role(actor.role, {ActorRole.WORKER})
    worker_id = actor.effective_worker_id
    now = _now_or(payload.now)
    try:
        if payload.change_type == "cover":
            request = service.request_cover(
                worker_id, payload.booking_id, payload.replacement_worker_id, payload.reason, now
            )
        else:
            request = service.request_release(worker_id, payload.booking_id, payload.reason, now)
    except ServiceError as exc:
        raise_service_error(exc)
    recorder.record(
        "change_request.created",
        "lifecycle",
        actor=actor,
        subject_type="shift_change_request",
        subject_id=request.request_id,
        worker_id=worker_id,
        context={"change_type": request.change_type, "booking_id": request.booking_id},
    )
    return _view(request, shifts, venues)


@router.get("/me/shift-change-requests", response_model=list[ShiftChangeResponse])
def list_my_change_requests(
    actor: ActorContext = Depends(get_actor_context),
    service: ShiftChangeService = Depends(get_shift_change_service),
    shifts: ShiftRepository = Depends(get_shift_repo),
    venues: OrganisationRepository = Depends(get_organisation_repo),
) -> list[ShiftChangeResponse]:
    require_role(actor.role, {ActorRole.WORKER})
    requests = service.list_requests_for_worker(actor.effective_worker_id)
    return _views(requests, shifts, venues)


@router.post("/me/shift-change-requests/{request_id}/accept-replacement", response_model=ShiftChangeResponse)
def accept_replacement(
    request_id: str,
    payload: ShiftChangeAnswerRequest,
    actor: ActorContext = Depends(get_actor_context),
    service: ShiftChangeService = Depends(get_shift_change_service),
    shifts: ShiftRepository = Depends(get_shift_repo),
    venues: OrganisationRepository = Depends(get_organisation_repo),
    recorder: EventRecorder = Depends(get_event_recorder),
) -> ShiftChangeResponse:
    require_role(actor.role, {ActorRole.WORKER})
    try:
        request = service.accept_replacement(
            request_id, actor.effective_worker_id, _now_or(payload.now)
        )
    except ServiceError as exc:
        raise_service_error(exc)
    recorder.record(
        "change_request.replacement_accepted", "lifecycle", actor=actor,
        subject_type="shift_change_request", subject_id=request_id,
        worker_id=actor.effective_worker_id, context={},
    )
    return _view(request, shifts, venues)


@router.post("/me/shift-change-requests/{request_id}/decline-replacement", response_model=ShiftChangeResponse)
def decline_replacement(
    request_id: str,
    payload: ShiftChangeAnswerRequest,
    actor: ActorContext = Depends(get_actor_context),
    service: ShiftChangeService = Depends(get_shift_change_service),
    shifts: ShiftRepository = Depends(get_shift_repo),
    venues: OrganisationRepository = Depends(get_organisation_repo),
    recorder: EventRecorder = Depends(get_event_recorder),
) -> ShiftChangeResponse:
    require_role(actor.role, {ActorRole.WORKER})
    try:
        request = service.decline_replacement(
            request_id, actor.effective_worker_id, _now_or(payload.now)
        )
    except ServiceError as exc:
        raise_service_error(exc)
    recorder.record(
        "change_request.replacement_declined", "lifecycle", actor=actor,
        subject_type="shift_change_request", subject_id=request_id,
        worker_id=actor.effective_worker_id, context={},
    )
    return _view(request, shifts, venues)


@router.post("/me/shift-change-requests/{request_id}/withdraw", response_model=ShiftChangeResponse)
def withdraw_change_request(
    request_id: str,
    payload: ShiftChangeAnswerRequest,
    actor: ActorContext = Depends(get_actor_context),
    service: ShiftChangeService = Depends(get_shift_change_service),
    shifts: ShiftRepository = Depends(get_shift_repo),
    venues: OrganisationRepository = Depends(get_organisation_repo),
    recorder: EventRecorder = Depends(get_event_recorder),
) -> ShiftChangeResponse:
    require_role(actor.role, {ActorRole.WORKER})
    try:
        request = service.withdraw(request_id, actor.effective_worker_id, _now_or(payload.now))
    except ServiceError as exc:
        raise_service_error(exc)
    recorder.record(
        "change_request.withdrawn", "lifecycle", actor=actor,
        subject_type="shift_change_request", subject_id=request_id,
        worker_id=actor.effective_worker_id, context={},
    )
    return _view(request, shifts, venues)


@router.get("/venues/me/shift-change-requests", response_model=list[ShiftChangeResponse])
def list_venue_change_requests(
    status: str | None = Query(default=None, max_length=24),
    actor: ActorContext = Depends(get_actor_context),
    service: ShiftChangeService = Depends(get_shift_change_service),
    shifts: ShiftRepository = Depends(get_shift_repo),
    venues: OrganisationRepository = Depends(get_organisation_repo),
) -> list[ShiftChangeResponse]:
    venue_id = _venue_of(actor)
    requests = service.list_requests_for_venue(venue_id, status)
    return _views(requests, shifts, venues)


@router.post("/venues/me/shift-change-requests/{request_id}/approve", response_model=ShiftChangeResponse)
def approve_change_request(
    request_id: str,
    payload: ShiftChangeAnswerRequest,
    actor: ActorContext = Depends(get_actor_context),
    service: ShiftChangeService = Depends(get_shift_change_service),
    shifts: ShiftRepository = Depends(get_shift_repo),
    venues: OrganisationRepository = Depends(get_organisation_repo),
    recorder: EventRecorder = Depends(get_event_recorder),
) -> ShiftChangeResponse:
    venue_id = _venue_of(actor)
    try:
        request = service.approve(request_id, venue_id, actor.user_id, _now_or(payload.now))
    except ServiceError as exc:
        raise_service_error(exc)
    recorder.record(
        "change_request.approved", "lifecycle", actor=actor,
        subject_type="shift_change_request", subject_id=request_id,
        worker_id=request.worker_id,
        context={"change_type": request.change_type, "booking_id": request.booking_id},
    )
    return _view(request, shifts, venues)


@router.post("/venues/me/shift-change-requests/{request_id}/decline", response_model=ShiftChangeResponse)
def decline_change_request(
    request_id: str,
    payload: ShiftChangeAnswerRequest,
    actor: ActorContext = Depends(get_actor_context),
    service: ShiftChangeService = Depends(get_shift_change_service),
    shifts: ShiftRepository = Depends(get_shift_repo),
    venues: OrganisationRepository = Depends(get_organisation_repo),
    recorder: EventRecorder = Depends(get_event_recorder),
) -> ShiftChangeResponse:
    venue_id = _venue_of(actor)
    try:
        request = service.decline(request_id, venue_id, actor.user_id, _now_or(payload.now))
    except ServiceError as exc:
        raise_service_error(exc)
    recorder.record(
        "change_request.declined", "lifecycle", actor=actor,
        subject_type="shift_change_request", subject_id=request_id,
        worker_id=request.worker_id, context={},
    )
    return _view(request, shifts, venues)


def _venue_of(actor: ActorContext) -> str:
    require_role(actor.role, {ActorRole.OPERATOR})
    if not actor.account_id:
        raise HTTPException(status_code=403, detail="This account is not linked to a venue.")
    return actor.account_id


def _views(
    requests: list[ShiftChangeRequest], shifts: ShiftRepository, venues: OrganisationRepository
) -> list[ShiftChangeResponse]:
    summaries = summarise_shifts([request.shift_id for request in requests], shifts, venues)
    return [_view_with(request, summaries) for request in requests]


def _view(
    request: ShiftChangeRequest, shifts: ShiftRepository, venues: OrganisationRepository
) -> ShiftChangeResponse:
    summaries = summarise_shifts([request.shift_id], shifts, venues)
    return _view_with(request, summaries)


def _view_with(request: ShiftChangeRequest, summaries) -> ShiftChangeResponse:
    return ShiftChangeResponse(
        request_id=request.request_id,
        booking_id=request.booking_id,
        shift_id=request.shift_id,
        venue_id=request.venue_id,
        worker_id=request.worker_id,
        change_type=request.change_type,
        status=request.status,
        reason=request.reason,
        replacement_worker_id=request.replacement_worker_id,
        created_at=request.created_at,
        updated_at=request.updated_at,
        decided_at=request.decided_at,
        decided_by_user_id=request.decided_by_user_id,
        shift=_summary_view(summaries.get(request.shift_id)),
    )

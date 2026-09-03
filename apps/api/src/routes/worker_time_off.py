from __future__ import annotations

from fastapi import APIRouter, Depends, Response

from apps.api.src.auth import ActorContext, ActorRole, get_actor_context, require_role
from apps.api.src.datetime_utils import utc_now
from apps.api.src.deps import (
    get_event_recorder,
    get_idempotency_service,
)
from apps.api.src.routes.availability_views import time_off_view
from apps.api.src.routes.idempotency_support import (
    IdempotencyKeyHeader,
    replayed,
    start_or_conflict,
)
from apps.api.src.routes.service_errors import raise_service_error
from apps.api.src.schemas_availability import TimeOffCreateRequest, TimeOffResponse
from apps.api.src.services.availability_management_service import AvailabilityManagementService
from apps.api.src.services.errors import ServiceError
from apps.api.src.services.event_recorder import EventRecorder
from apps.api.src.services.idempotency import IdempotencyService
from apps.api.src.service_dependencies_availability import get_availability_management_service

router = APIRouter(tags=["worker time off"])


@router.get("/me/time-off", response_model=list[TimeOffResponse])
def list_time_off(
    actor: ActorContext = Depends(get_actor_context),
    service: AvailabilityManagementService = Depends(get_availability_management_service),
) -> list[TimeOffResponse]:
    worker_id = _worker_of(actor)
    return [time_off_view(item) for item in service.list_time_off_for_worker(worker_id)]


@router.post("/me/time-off", response_model=TimeOffResponse, status_code=201)
def request_time_off(
    payload: TimeOffCreateRequest,
    response: Response,
    idempotency_key: IdempotencyKeyHeader = None,
    actor: ActorContext = Depends(get_actor_context),
    service: AvailabilityManagementService = Depends(get_availability_management_service),
    idempotency: IdempotencyService = Depends(get_idempotency_service),
    recorder: EventRecorder = Depends(get_event_recorder),
) -> TimeOffResponse:
    worker_id = _worker_of(actor)
    started = start_or_conflict(
        idempotency,
        actor.user_id,
        "time_off.request",
        idempotency_key,
        payload.model_dump(mode="json"),
    )
    if started.cached_response is not None:
        return replayed(response, TimeOffResponse, started.cached_response)
    try:
        item = service.request_time_off(
            worker_id,
            payload.venue_id,
            payload.start_time,
            payload.end_time,
            payload.reason,
            utc_now(),
        )
    except ServiceError as exc:
        raise_service_error(exc)
    recorder.record(
        "time_off.requested",
        "lifecycle",
        actor=actor,
        venue_id=item.venue_id,
        subject_type="time_off_request",
        subject_id=item.request_id,
    )
    result = time_off_view(item)
    idempotency.finish(started.record_id, result.model_dump(mode="json"))
    return result


@router.post("/me/time-off/{request_id}/withdraw", response_model=TimeOffResponse)
def withdraw_time_off(
    request_id: str,
    response: Response,
    idempotency_key: IdempotencyKeyHeader = None,
    actor: ActorContext = Depends(get_actor_context),
    service: AvailabilityManagementService = Depends(get_availability_management_service),
    idempotency: IdempotencyService = Depends(get_idempotency_service),
    recorder: EventRecorder = Depends(get_event_recorder),
) -> TimeOffResponse:
    worker_id = _worker_of(actor)
    started = start_or_conflict(
        idempotency,
        actor.user_id,
        "time_off.withdraw",
        idempotency_key,
        {"request_id": request_id},
    )
    if started.cached_response is not None:
        return replayed(response, TimeOffResponse, started.cached_response)
    try:
        item = service.withdraw_time_off(worker_id, request_id, utc_now())
    except ServiceError as exc:
        raise_service_error(exc)
    recorder.record(
        "time_off.withdrawn",
        "lifecycle",
        actor=actor,
        venue_id=item.venue_id,
        subject_type="time_off_request",
        subject_id=item.request_id,
    )
    result = time_off_view(item)
    idempotency.finish(started.record_id, result.model_dump(mode="json"))
    return result


def _worker_of(actor: ActorContext) -> str:
    require_role(actor.role, {ActorRole.WORKER})
    return actor.effective_worker_id

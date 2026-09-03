from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, Response

from apps.api.src.auth import ActorContext, ActorRole, get_actor_context, require_role
from apps.api.src.datetime_utils import utc_now
from apps.api.src.deps import (
    get_event_recorder,
    get_idempotency_service,
)
from apps.api.src.models.availability import TimeOffStatus
from apps.api.src.routes.availability_views import time_off_view
from apps.api.src.routes.idempotency_support import (
    IdempotencyKeyHeader,
    replayed,
    start_or_conflict,
)
from apps.api.src.routes.service_errors import raise_service_error
from apps.api.src.schemas_availability import TimeOffResponse
from apps.api.src.services.availability_management_service import AvailabilityManagementService
from apps.api.src.services.errors import ServiceError
from apps.api.src.services.event_recorder import EventRecorder
from apps.api.src.services.idempotency import IdempotencyService
from apps.api.src.service_dependencies_availability import get_availability_management_service
from apps.api.src.validation_types import UtcTimestamp

router = APIRouter(tags=["venue time off"])


@router.get("/venues/me/time-off", response_model=list[TimeOffResponse])
def list_time_off(
    status: TimeOffStatus | None = None,
    starts_from: UtcTimestamp | None = Query(default=None),
    starts_before: UtcTimestamp | None = Query(default=None),
    actor: ActorContext = Depends(get_actor_context),
    service: AvailabilityManagementService = Depends(get_availability_management_service),
) -> list[TimeOffResponse]:
    venue_id = _venue_of(actor)
    try:
        items = service.list_time_off_for_venue(
            venue_id, status, starts_from, starts_before
        )
    except ServiceError as exc:
        raise_service_error(exc)
    return [time_off_view(item) for item in items]


@router.post("/venues/me/time-off/{request_id}/approve", response_model=TimeOffResponse)
def approve_time_off(
    request_id: str,
    response: Response,
    idempotency_key: IdempotencyKeyHeader = None,
    actor: ActorContext = Depends(get_actor_context),
    service: AvailabilityManagementService = Depends(get_availability_management_service),
    idempotency: IdempotencyService = Depends(get_idempotency_service),
    recorder: EventRecorder = Depends(get_event_recorder),
) -> TimeOffResponse:
    return _decide(
        "approve", request_id, response, idempotency_key, actor, service, idempotency, recorder
    )


@router.post("/venues/me/time-off/{request_id}/decline", response_model=TimeOffResponse)
def decline_time_off(
    request_id: str,
    response: Response,
    idempotency_key: IdempotencyKeyHeader = None,
    actor: ActorContext = Depends(get_actor_context),
    service: AvailabilityManagementService = Depends(get_availability_management_service),
    idempotency: IdempotencyService = Depends(get_idempotency_service),
    recorder: EventRecorder = Depends(get_event_recorder),
) -> TimeOffResponse:
    return _decide(
        "decline", request_id, response, idempotency_key, actor, service, idempotency, recorder
    )


def _decide(
    action: str,
    request_id: str,
    response: Response,
    idempotency_key: str | None,
    actor: ActorContext,
    service: AvailabilityManagementService,
    idempotency: IdempotencyService,
    recorder: EventRecorder,
) -> TimeOffResponse:
    venue_id = _venue_of(actor)
    started = start_or_conflict(
        idempotency,
        actor.user_id,
        f"time_off.{action}",
        idempotency_key,
        {"request_id": request_id},
    )
    if started.cached_response is not None:
        return replayed(response, TimeOffResponse, started.cached_response)
    try:
        if action == "approve":
            item = service.approve_time_off(venue_id, request_id, actor.user_id, utc_now())
        else:
            item = service.decline_time_off(venue_id, request_id, actor.user_id, utc_now())
    except ServiceError as exc:
        raise_service_error(exc)
    recorder.record(
        f"time_off.{action}d",
        "lifecycle",
        actor=actor,
        venue_id=venue_id,
        worker_id=item.worker_id,
        subject_type="time_off_request",
        subject_id=item.request_id,
    )
    result = time_off_view(item)
    idempotency.finish(started.record_id, result.model_dump(mode="json"))
    return result


def _venue_of(actor: ActorContext) -> str:
    require_role(actor.role, {ActorRole.OPERATOR})
    if not actor.account_id:
        raise HTTPException(status_code=403, detail="This account is not linked to a venue.")
    return actor.account_id

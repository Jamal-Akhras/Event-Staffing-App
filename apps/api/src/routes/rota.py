from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response

from apps.api.src.auth import ActorContext, ActorRole, get_actor_context, require_role
from apps.api.src.datetime_utils import utc_now
from apps.api.src.deps import get_idempotency_service, get_rota_service
from apps.api.src.models.rota_publication import RotaPublication
from apps.api.src.rate_limit import actor_or_ip, limiter
from apps.api.src.routes.idempotency_support import IdempotencyKeyHeader, replayed
from apps.api.src.routes.service_errors import raise_service_error
from apps.api.src.schemas import ShiftResponse
from apps.api.src.schemas_rota import (
    RotaPublicationResponse,
    RotaPublishRequest,
    RotaPublishResponse,
    RotaReassignRequest,
    RotaRemoveRequest,
    RotaTimesRequest,
)
from apps.api.src.services.errors import ServiceError
from apps.api.src.services.event_recorder import EventRecorder
from apps.api.src.deps import get_event_recorder
from apps.api.src.services.idempotency import IdempotencyConflict, IdempotencyService
from apps.api.src.services.rota_service import RotaService
from apps.api.src.helpers import _now_or, _shift_view

router = APIRouter(tags=["rota"])


@router.post("/venues/me/rota/publish", response_model=RotaPublishResponse)
@limiter.limit("30/hour", key_func=actor_or_ip)
def publish_rota(
    request: Request,
    payload: RotaPublishRequest,
    response: Response,
    idempotency_key: IdempotencyKeyHeader = None,
    idempotency: IdempotencyService = Depends(get_idempotency_service),
    service: RotaService = Depends(get_rota_service),
    actor: ActorContext = Depends(get_actor_context),
    recorder: EventRecorder = Depends(get_event_recorder),
) -> RotaPublishResponse:
    venue_id = _venue_of(actor)
    try:
        started = idempotency.start(
            actor.user_id, "rota.publish", idempotency_key, payload.model_dump(mode="json")
        )
    except IdempotencyConflict as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    if started.cached_response is not None:
        return replayed(response, RotaPublishResponse, started.cached_response)

    try:
        outcome = service.publish(venue_id, payload.week_start, actor.user_id, _now_or(payload.now))
    except ServiceError as exc:
        raise_service_error(exc)
    recorder.record(
        "rota.published",
        "lifecycle",
        actor=actor,
        subject_type="rota_publication",
        subject_id=outcome.publication.publication_id,
        context={
            "week_start": str(outcome.publication.week_start),
            "revision": outcome.publication.revision,
            "booked": len(outcome.booked_worker_ids),
            "offered": len(outcome.offered_worker_ids),
            "changes": len(outcome.changes),
        },
    )
    result = RotaPublishResponse(
        publication=_publication_view(outcome.publication, outcome.changes),
        booked_worker_ids=outcome.booked_worker_ids,
        offered_worker_ids=outcome.offered_worker_ids,
    )
    idempotency.finish(started.record_id, result.model_dump(mode="json"))
    return result


@router.get("/venues/me/rota/publications", response_model=list[RotaPublicationResponse])
def list_publications(
    week_start: date = Query(...),
    service: RotaService = Depends(get_rota_service),
    actor: ActorContext = Depends(get_actor_context),
) -> list[RotaPublicationResponse]:
    venue_id = _venue_of(actor)
    return [
        _publication_view(publication, changes)
        for publication, changes in service.publications_for_week(venue_id, week_start)
    ]


@router.post("/venues/me/rota/shifts/{shift_id}/times", response_model=ShiftResponse)
def update_shift_times(
    shift_id: str,
    payload: RotaTimesRequest,
    service: RotaService = Depends(get_rota_service),
    actor: ActorContext = Depends(get_actor_context),
) -> ShiftResponse:
    venue_id = _venue_of(actor)
    try:
        shift = service.update_times(
            venue_id, shift_id, payload.start_time, payload.end_time, actor.user_id, _now_or(payload.now)
        )
    except ServiceError as exc:
        raise_service_error(exc)
    return _shift_view(shift)


@router.post("/venues/me/rota/shifts/{shift_id}/reassign", response_model=ShiftResponse)
def reassign_shift(
    shift_id: str,
    payload: RotaReassignRequest,
    service: RotaService = Depends(get_rota_service),
    actor: ActorContext = Depends(get_actor_context),
) -> ShiftResponse:
    venue_id = _venue_of(actor)
    try:
        shift = service.reassign(venue_id, shift_id, payload.worker_id, actor.user_id, _now_or(payload.now))
    except ServiceError as exc:
        raise_service_error(exc)
    return _shift_view(shift)


@router.post("/venues/me/rota/shifts/{shift_id}/remove", response_model=ShiftResponse)
def remove_shift(
    shift_id: str,
    payload: RotaRemoveRequest,
    service: RotaService = Depends(get_rota_service),
    actor: ActorContext = Depends(get_actor_context),
) -> ShiftResponse:
    venue_id = _venue_of(actor)
    try:
        shift = service.remove(venue_id, shift_id, payload.reason, actor.user_id, _now_or(payload.now))
    except ServiceError as exc:
        raise_service_error(exc)
    return _shift_view(shift)


def _venue_of(actor: ActorContext) -> str:
    require_role(actor.role, {ActorRole.OPERATOR})
    if not actor.account_id:
        raise HTTPException(status_code=403, detail="This account is not linked to a venue.")
    return actor.account_id


def _publication_view(publication: RotaPublication, changes: list[dict]) -> RotaPublicationResponse:
    return RotaPublicationResponse(
        publication_id=publication.publication_id,
        venue_id=publication.venue_id,
        week_start=publication.week_start,
        revision=publication.revision,
        published_at=publication.published_at,
        published_by_user_id=publication.published_by_user_id,
        assignments=publication.assignments,
        changes=changes,
    )

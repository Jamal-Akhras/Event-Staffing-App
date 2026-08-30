from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, Query, Request

from apps.api.src.auth import ActorContext, ActorRole, get_actor_context, require_role
from apps.api.src.deps import get_event_recorder, get_event_repo
from apps.api.src.models.event import Event, EventQuery
from apps.api.src.rate_limit import actor_or_ip, limiter
from apps.api.src.repositories.event_repository import EventRepository
from apps.api.src.schemas_events import (
    EventCounts,
    EventIngestRequest,
    EventIngestResponse,
    EventPage,
    EventResponse,
)
from apps.api.src.services.event_recorder import EventRecorder

router = APIRouter(tags=["events"])


@router.post("/events", response_model=EventIngestResponse, status_code=202)
@limiter.limit("1000/hour", key_func=actor_or_ip)
def ingest_events(
    request: Request,
    payload: EventIngestRequest,
    actor: ActorContext = Depends(get_actor_context),
    recorder: EventRecorder = Depends(get_event_recorder),
) -> EventIngestResponse:
    require_role(actor.role, {ActorRole.WORKER, ActorRole.OPERATOR})
    for item in payload.events:
        recorder.record(
            item.name,
            "behaviour",
            actor=actor,
            subject_type=item.subject_type,
            subject_id=item.subject_id,
            context=item.context,
            occurred_at=item.occurred_at,
            slate_id=item.slate_id,
            position=item.position,
            dwell_ms=item.dwell_ms,
            event_version=item.event_version,
        )
    return EventIngestResponse(recorded=len(payload.events))


@router.get("/system/events", response_model=EventPage)
def query_events(
    name: str | None = None,
    category: str | None = None,
    source: str | None = None,
    actor_user_id: str | None = None,
    venue_id: str | None = None,
    worker_id: str | None = None,
    subject_type: str | None = None,
    subject_id: str | None = None,
    slate_id: str | None = None,
    since: datetime | None = None,
    until: datetime | None = None,
    before_id: str | None = None,
    limit: int = Query(default=100, ge=1, le=500),
    actor: ActorContext = Depends(get_actor_context),
    repo: EventRepository = Depends(get_event_repo),
) -> EventPage:
    require_role(actor.role, {ActorRole.SYSTEM})
    events = repo.query(
        EventQuery(
            name=name,
            category=category,
            source=source,
            actor_user_id=actor_user_id,
            venue_id=venue_id,
            worker_id=worker_id,
            subject_type=subject_type,
            subject_id=subject_id,
            slate_id=slate_id,
            since=since,
            until=until,
            before_id=before_id,
            limit=limit,
        )
    )
    return _page(events, limit)


@router.get("/system/events/counts", response_model=EventCounts)
def count_events(
    category: str | None = None,
    source: str | None = None,
    venue_id: str | None = None,
    since: datetime | None = None,
    until: datetime | None = None,
    actor: ActorContext = Depends(get_actor_context),
    repo: EventRepository = Depends(get_event_repo),
) -> EventCounts:
    require_role(actor.role, {ActorRole.SYSTEM})
    counts = repo.count_by_name(
        EventQuery(category=category, source=source, venue_id=venue_id, since=since, until=until)
    )
    return EventCounts(counts=counts)


@router.get("/activity", response_model=EventPage)
def my_activity(
    name: str | None = None,
    category: str | None = None,
    subject_type: str | None = None,
    subject_id: str | None = None,
    since: datetime | None = None,
    before_id: str | None = None,
    limit: int = Query(default=50, ge=1, le=200),
    actor: ActorContext = Depends(get_actor_context),
    repo: EventRepository = Depends(get_event_repo),
) -> EventPage:
    require_role(actor.role, {ActorRole.OPERATOR, ActorRole.WORKER})
    scope = (
        {"venue_id": actor.account_id}
        if actor.role == ActorRole.OPERATOR
        else {"worker_id": actor.effective_worker_id}
    )
    events = repo.query(
        EventQuery(
            name=name,
            category=category,
            subject_type=subject_type,
            subject_id=subject_id,
            since=since,
            before_id=before_id,
            limit=limit,
            **scope,
        )
    )
    return _page(events, limit)


def _page(events: list[Event], limit: int) -> EventPage:
    return EventPage(
        events=[EventResponse(**event.__dict__) for event in events],
        next_before_id=events[-1].event_id if len(events) == limit else None,
    )

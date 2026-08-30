from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from apps.api.src.validation_types import UtcTimestamp

NAME_PATTERN = r"^[a-z][a-z0-9_]*(\.[a-z][a-z0-9_]*)+$"


class ClientEvent(BaseModel):
    name: str = Field(pattern=NAME_PATTERN, max_length=80)
    occurred_at: UtcTimestamp | None = None
    subject_type: str | None = Field(default=None, max_length=40)
    subject_id: str | None = Field(default=None, max_length=200)
    context: dict[str, Any] = Field(default_factory=dict)
    slate_id: str | None = Field(default=None, max_length=64)
    position: int | None = Field(default=None, ge=0, le=10_000)
    dwell_ms: int | None = Field(default=None, ge=0, le=86_400_000)
    event_version: int = Field(default=1, ge=1, le=1_000)


class EventIngestRequest(BaseModel):
    events: list[ClientEvent] = Field(min_length=1, max_length=50)


class EventIngestResponse(BaseModel):
    recorded: int


class EventResponse(BaseModel):
    event_id: str
    occurred_at: UtcTimestamp
    recorded_at: UtcTimestamp
    name: str
    category: str
    source: str
    actor_user_id: str | None
    actor_role: str | None
    organisation_id: str | None
    venue_id: str | None
    worker_id: str | None
    subject_type: str | None
    subject_id: str | None
    context: dict[str, Any]
    request_id: str | None
    session_id: str | None
    ip: str | None
    user_agent: str | None
    app_version: str | None
    status_code: int | None
    duration_ms: int | None
    slate_id: str | None
    position: int | None
    dwell_ms: int | None
    event_version: int


class EventPage(BaseModel):
    events: list[EventResponse]
    next_before_id: str | None = None


class EventCounts(BaseModel):
    counts: dict[str, int]

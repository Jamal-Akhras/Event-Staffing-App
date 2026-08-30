from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass(frozen=True)
class Event:
    event_id: str
    occurred_at: datetime
    recorded_at: datetime
    name: str
    category: str
    source: str
    actor_user_id: str | None = None
    actor_role: str | None = None
    organisation_id: str | None = None
    venue_id: str | None = None
    worker_id: str | None = None
    subject_type: str | None = None
    subject_id: str | None = None
    context: dict[str, Any] = field(default_factory=dict)
    request_id: str | None = None
    session_id: str | None = None
    ip: str | None = None
    user_agent: str | None = None
    app_version: str | None = None
    status_code: int | None = None
    duration_ms: int | None = None
    slate_id: str | None = None
    position: int | None = None
    dwell_ms: int | None = None
    event_version: int = 1


@dataclass(frozen=True)
class EventQuery:
    name: str | None = None
    category: str | None = None
    source: str | None = None
    actor_user_id: str | None = None
    venue_id: str | None = None
    worker_id: str | None = None
    subject_type: str | None = None
    subject_id: str | None = None
    slate_id: str | None = None
    since: datetime | None = None
    until: datetime | None = None
    before_id: str | None = None
    limit: int = 100

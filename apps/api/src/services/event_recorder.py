from __future__ import annotations

import json
from datetime import datetime
from typing import Any
from uuid import uuid4

from apps.api.src.auth.actor import ActorContext
from apps.api.src.datetime_utils import utc_now
from apps.api.src.models.event import Event
from apps.api.src.repositories.event_repository import EventRepository
from apps.api.src.request_context import RequestMetadata, current_request_metadata

SECRET_HINTS = ("password", "token", "secret", "authorization", "code_verifier", "hashed")
MAX_CONTEXT_CHARS = 4000

CATEGORIES = {"audit", "lifecycle", "behaviour", "auth", "money", "system"}


def redact(context: dict[str, Any] | None) -> dict[str, Any]:
    if not context:
        return {}
    cleaned = {
        key: ("[redacted]" if any(hint in key.lower() for hint in SECRET_HINTS) else value)
        for key, value in context.items()
    }
    encoded = json.dumps(cleaned, default=str)
    if len(encoded) > MAX_CONTEXT_CHARS:
        return {"truncated": True, "size": len(encoded)}
    return json.loads(encoded)


class EventRecorder:
    def __init__(self, repo: EventRepository, metadata: RequestMetadata | None = None) -> None:
        self._repo = repo
        self._metadata = metadata

    @property
    def metadata(self) -> RequestMetadata:
        return self._metadata or current_request_metadata()

    def record(
        self,
        name: str,
        category: str,
        *,
        actor: ActorContext | None = None,
        actor_user_id: str | None = None,
        actor_role: str | None = None,
        venue_id: str | None = None,
        organisation_id: str | None = None,
        worker_id: str | None = None,
        subject_type: str | None = None,
        subject_id: str | None = None,
        context: dict[str, Any] | None = None,
        occurred_at: datetime | None = None,
        status_code: int | None = None,
        duration_ms: int | None = None,
        source: str | None = None,
        slate_id: str | None = None,
        position: int | None = None,
        dwell_ms: int | None = None,
        event_version: int = 1,
    ) -> Event:
        if category not in CATEGORIES:
            raise ValueError(f"Unknown event category: {category}")
        metadata = self.metadata
        now = utc_now()
        event = Event(
            event_id=str(uuid4()),
            occurred_at=occurred_at or now,
            recorded_at=now,
            name=name,
            category=category,
            source=source or metadata.source,
            actor_user_id=actor.user_id if actor else actor_user_id,
            actor_role=actor.role.value if actor else actor_role,
            organisation_id=organisation_id or (actor.organisation_id if actor else None),
            venue_id=venue_id or (actor.account_id if actor else None),
            worker_id=worker_id or (actor.worker_profile_id if actor else None),
            subject_type=subject_type,
            subject_id=subject_id,
            context=redact(context),
            request_id=metadata.request_id,
            session_id=metadata.session_id,
            ip=metadata.ip,
            user_agent=metadata.user_agent,
            app_version=metadata.app_version,
            status_code=status_code,
            duration_ms=duration_ms,
            slate_id=slate_id,
            position=position,
            dwell_ms=dwell_ms,
            event_version=event_version,
        )
        return self._repo.append(event)

from __future__ import annotations

from typing import Any

from apps.api.src.config import use_in_memory_repositories
from apps.api.src.request_context import RequestMetadata
from apps.api.src.services.event_recorder import EventRecorder


def record_durable(name: str, category: str, metadata: RequestMetadata | None = None, **fields: Any) -> None:
    if use_in_memory_repositories():
        from apps.api.src.repository_dependencies import shared_event_repository

        EventRecorder(shared_event_repository(), metadata).record(name, category, **fields)
        return

    from apps.api.src.db.database import SessionLocal
    from apps.api.src.repositories.sqlalchemy_event_repository import SqlAlchemyEventRepository

    with SessionLocal() as session:
        EventRecorder(SqlAlchemyEventRepository(session), metadata).record(name, category, **fields)
        session.commit()

from __future__ import annotations

from sqlalchemy import Column, Index, Integer, JSON, String

from apps.api.src.db.database import Base
from apps.api.src.db.types import UtcDateTime


class EventModel(Base):
    __tablename__ = "events"
    __table_args__ = (
        Index("ix_events_occurred", "occurred_at"),
        Index("ix_events_recorded", "recorded_at", "event_id"),
        Index("ix_events_name_occurred", "name", "occurred_at"),
        Index("ix_events_actor_occurred", "actor_user_id", "occurred_at"),
        Index("ix_events_venue_occurred", "venue_id", "occurred_at"),
        Index("ix_events_worker_occurred", "worker_id", "occurred_at"),
        Index("ix_events_subject", "subject_type", "subject_id", "occurred_at"),
        Index("ix_events_category_occurred", "category", "occurred_at"),
        Index("ix_events_slate", "slate_id"),
    )

    event_id = Column(String, primary_key=True)
    occurred_at = Column(UtcDateTime(), nullable=False)
    recorded_at = Column(UtcDateTime(), nullable=False)
    name = Column(String(80), nullable=False)
    category = Column(String(32), nullable=False)
    source = Column(String(20), nullable=False)
    actor_user_id = Column(String, nullable=True)
    actor_role = Column(String(20), nullable=True)
    organisation_id = Column(String, nullable=True)
    venue_id = Column(String, nullable=True)
    worker_id = Column(String, nullable=True)
    subject_type = Column(String(40), nullable=True)
    subject_id = Column(String, nullable=True)
    context = Column(JSON, nullable=False, default=dict)
    request_id = Column(String(64), nullable=True)
    session_id = Column(String(64), nullable=True)
    ip = Column(String(45), nullable=True)
    user_agent = Column(String(400), nullable=True)
    app_version = Column(String(40), nullable=True)
    status_code = Column(Integer, nullable=True)
    duration_ms = Column(Integer, nullable=True)
    slate_id = Column(String(64), nullable=True)
    position = Column(Integer, nullable=True)
    dwell_ms = Column(Integer, nullable=True)
    event_version = Column(Integer, nullable=False, default=1)

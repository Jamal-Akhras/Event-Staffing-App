from __future__ import annotations

from sqlalchemy import CheckConstraint, Column, Index, String

from apps.api.src.db.database import Base
from apps.api.src.db.types import UtcDateTime


class ConsentEventModel(Base):
    __tablename__ = "consent_events"
    __table_args__ = (
        CheckConstraint(
            "action IN ('granted', 'withdrawn', 'objected', 'acknowledged')",
            name="ck_consent_events_action",
        ),
        Index("ix_consent_events_user_purpose", "user_id", "purpose", "occurred_at"),
    )

    event_id = Column(String, primary_key=True)
    user_id = Column(String, nullable=False)
    purpose = Column(String(32), nullable=False)
    action = Column(String(12), nullable=False)
    basis = Column(String(32), nullable=False)
    policy_version = Column(String(32), nullable=False)
    source = Column(String(32), nullable=False)
    occurred_at = Column(UtcDateTime(), nullable=False)

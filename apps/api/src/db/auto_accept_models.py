from __future__ import annotations

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    ForeignKey,
    Index,
    Integer,
    JSON,
    Numeric,
    String,
    UniqueConstraint,
)

from apps.api.src.db.database import Base
from apps.api.src.db.types import UtcDateTime


class WorkerAutoAcceptRuleModel(Base):
    __tablename__ = "worker_auto_accept_rules"
    __table_args__ = (
        CheckConstraint(
            "minimum_rate IS NULL OR minimum_rate >= 0",
            name="ck_auto_accept_rules_minimum_rate",
        ),
        CheckConstraint(
            "minimum_notice_hours IS NULL OR minimum_notice_hours >= 0",
            name="ck_auto_accept_rules_minimum_notice",
        ),
        CheckConstraint("version >= 1", name="ck_auto_accept_rules_version"),
        UniqueConstraint(
            "worker_id", "venue_id", name="uq_auto_accept_rules_worker_venue"
        ),
    )

    rule_id = Column(String, primary_key=True)
    worker_id = Column(String, nullable=False)
    venue_id = Column(String, ForeignKey("venues.venue_id", ondelete="RESTRICT"), nullable=False)
    enabled = Column(Boolean, nullable=False)
    roles = Column(JSON, nullable=False)
    minimum_rate = Column(Numeric(12, 2), nullable=True)
    minimum_notice_hours = Column(Integer, nullable=True)
    version = Column(Integer, nullable=False)
    created_at = Column(UtcDateTime(), nullable=False)
    updated_at = Column(UtcDateTime(), nullable=False)


class AutoAcceptAttemptModel(Base):
    __tablename__ = "auto_accept_attempts"
    __table_args__ = (
        CheckConstraint(
            "outcome IN ('accepted', 'skipped', 'failed')",
            name="ck_auto_accept_attempts_outcome",
        ),
        CheckConstraint(
            "rule_version >= 0", name="ck_auto_accept_attempts_rule_version"
        ),
        UniqueConstraint(
            "offer_id",
            "rule_version",
            name="uq_auto_accept_attempts_offer_rule_version",
        ),
        Index("ix_auto_accept_attempts_evaluated", "evaluated_at"),
    )

    attempt_id = Column(String, primary_key=True)
    offer_id = Column(
        String, ForeignKey("shift_offers.offer_id", ondelete="RESTRICT"), nullable=False
    )
    rule_id = Column(String, nullable=True)
    rule_version = Column(Integer, nullable=False)
    rule_snapshot = Column(JSON, nullable=False)
    evaluated_at = Column(UtcDateTime(), nullable=False)
    outcome = Column(String(12), nullable=False)
    reason = Column(String(500), nullable=True)

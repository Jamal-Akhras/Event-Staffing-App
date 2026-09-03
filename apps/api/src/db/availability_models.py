from __future__ import annotations

from sqlalchemy import CheckConstraint, Column, Date, ForeignKey, Index, Integer, String, extract

from apps.api.src.db.database import Base
from apps.api.src.db.types import UtcDateTime

_MAX_INTERVAL_SECONDS = 366 * 24 * 60 * 60


class AvailabilityRuleModel(Base):
    __tablename__ = "worker_availability_rules"
    __table_args__ = (
        CheckConstraint("weekday BETWEEN 0 AND 6", name="ck_availability_rules_weekday"),
        CheckConstraint(
            "start_minute BETWEEN 0 AND 1439", name="ck_availability_rules_start_minute"
        ),
        CheckConstraint(
            "duration_minutes BETWEEN 1 AND 1440", name="ck_availability_rules_duration"
        ),
        CheckConstraint(
            "effective_until IS NULL OR effective_until >= effective_from",
            name="ck_availability_rules_effective_dates",
        ),
        Index(
            "ix_availability_rules_worker_effective",
            "worker_id",
            "effective_from",
            "effective_until",
        ),
    )

    rule_id = Column(String, primary_key=True)
    worker_id = Column(
        String,
        ForeignKey("worker_profiles.worker_id", ondelete="CASCADE"),
        nullable=False,
    )
    timezone = Column(String(100), nullable=False)
    weekday = Column(Integer, nullable=False)
    start_minute = Column(Integer, nullable=False)
    duration_minutes = Column(Integer, nullable=False)
    effective_from = Column(Date, nullable=False)
    effective_until = Column(Date, nullable=True)
    created_at = Column(UtcDateTime(), nullable=False)
    updated_at = Column(UtcDateTime(), nullable=False)


class AvailabilityExceptionModel(Base):
    __tablename__ = "worker_availability_exceptions"

    exception_id = Column(String, primary_key=True)
    worker_id = Column(
        String,
        ForeignKey("worker_profiles.worker_id", ondelete="CASCADE"),
        nullable=False,
    )
    kind = Column(String(16), nullable=False)
    start_time = Column(UtcDateTime(), nullable=False)
    end_time = Column(UtcDateTime(), nullable=False)
    note = Column(String(500), nullable=True)
    created_at = Column(UtcDateTime(), nullable=False)
    updated_at = Column(UtcDateTime(), nullable=False)

    __table_args__ = (
        CheckConstraint("kind IN ('available', 'unavailable')", name="ck_availability_exceptions_kind"),
        CheckConstraint("end_time > start_time", name="ck_availability_exceptions_time_order"),
        CheckConstraint(
            extract("epoch", end_time) - extract("epoch", start_time) <= _MAX_INTERVAL_SECONDS,
            name="ck_availability_exceptions_max_interval",
        ),
        Index(
            "ix_availability_exceptions_worker_interval", "worker_id", "start_time", "end_time"
        ),
    )


class TimeOffRequestModel(Base):
    __tablename__ = "time_off_requests"

    request_id = Column(String, primary_key=True)
    worker_id = Column(
        String,
        ForeignKey("worker_profiles.worker_id", ondelete="CASCADE"),
        nullable=False,
    )
    venue_id = Column(String, ForeignKey("venues.venue_id", ondelete="RESTRICT"), nullable=False)
    start_time = Column(UtcDateTime(), nullable=False)
    end_time = Column(UtcDateTime(), nullable=False)
    status = Column(String(16), nullable=False)
    reason = Column(String(1000), nullable=False)
    created_at = Column(UtcDateTime(), nullable=False)
    updated_at = Column(UtcDateTime(), nullable=False)
    decided_at = Column(UtcDateTime(), nullable=True)
    decided_by_user_id = Column(String, nullable=True)

    __table_args__ = (
        CheckConstraint(
            "status IN ('pending', 'approved', 'declined', 'withdrawn')",
            name="ck_time_off_requests_status",
        ),
        CheckConstraint("end_time > start_time", name="ck_time_off_requests_time_order"),
        CheckConstraint(
            extract("epoch", end_time) - extract("epoch", start_time) <= _MAX_INTERVAL_SECONDS,
            name="ck_time_off_requests_max_interval",
        ),
        CheckConstraint(
            "((status IN ('approved', 'declined')) AND decided_at IS NOT NULL "
            "AND decided_by_user_id IS NOT NULL) OR "
            "((status IN ('pending', 'withdrawn')) AND decided_at IS NULL "
            "AND decided_by_user_id IS NULL)",
            name="ck_time_off_requests_decision_metadata",
        ),
        Index(
            "ix_time_off_requests_venue_status_start", "venue_id", "status", "start_time"
        ),
        Index(
            "ix_time_off_requests_worker_interval", "worker_id", "start_time", "end_time"
        ),
    )

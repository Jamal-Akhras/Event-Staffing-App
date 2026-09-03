from __future__ import annotations

from sqlalchemy import CheckConstraint, Column, ForeignKey, Index, String, text

from apps.api.src.db.database import Base
from apps.api.src.db.types import UtcDateTime


class ShiftChangeRequestModel(Base):
    __tablename__ = "shift_change_requests"
    __table_args__ = (
        CheckConstraint("change_type IN ('release', 'cover')", name="ck_shift_changes_type"),
        CheckConstraint(
            "status IN ('pending_replacement', 'pending_manager', 'approved', 'declined', "
            "'withdrawn', 'expired')",
            name="ck_shift_changes_status",
        ),
        CheckConstraint(
            "(change_type = 'cover') = (replacement_worker_id IS NOT NULL)",
            name="ck_shift_changes_replacement",
        ),
        CheckConstraint(
            "(status IN ('approved', 'declined')) = "
            "(decided_at IS NOT NULL AND decided_by_user_id IS NOT NULL)",
            name="ck_shift_changes_decision",
        ),
        CheckConstraint(
            "status <> 'pending_replacement' OR change_type = 'cover'",
            name="ck_shift_changes_replacement_wait",
        ),
        Index("ix_shift_changes_worker", "worker_id", "created_at"),
        Index("ix_shift_changes_venue_status", "venue_id", "status"),
        Index(
            "uq_shift_changes_one_pending",
            "booking_id",
            unique=True,
            postgresql_where=text("status IN ('pending_replacement', 'pending_manager')"),
            sqlite_where=text("status IN ('pending_replacement', 'pending_manager')"),
        ),
    )

    request_id = Column(String, primary_key=True)
    booking_id = Column(String, ForeignKey("bookings.booking_id", ondelete="RESTRICT"), nullable=False)
    shift_id = Column(String, ForeignKey("shifts.shift_id", ondelete="RESTRICT"), nullable=False)
    venue_id = Column(String, ForeignKey("venues.venue_id", ondelete="RESTRICT"), nullable=False)
    worker_id = Column(String, nullable=False)
    change_type = Column(String(12), nullable=False)
    status = Column(String(24), nullable=False)
    reason = Column(String(500), nullable=False)
    replacement_worker_id = Column(String, nullable=True)
    created_at = Column(UtcDateTime(), nullable=False)
    updated_at = Column(UtcDateTime(), nullable=False)
    decided_at = Column(UtcDateTime(), nullable=True)
    decided_by_user_id = Column(String, nullable=True)


class ShiftChangeTransitionModel(Base):
    __tablename__ = "shift_change_request_transitions"
    __table_args__ = (
        Index("ix_shift_change_transitions_request", "request_id", "occurred_at"),
    )

    transition_id = Column(String, primary_key=True)
    request_id = Column(
        String, ForeignKey("shift_change_requests.request_id", ondelete="CASCADE"), nullable=False
    )
    from_status = Column(String(24), nullable=True)
    to_status = Column(String(24), nullable=False)
    occurred_at = Column(UtcDateTime(), nullable=False)
    actor_user_id = Column(String, nullable=True)
    actor_role = Column(String(20), nullable=True)
    note = Column(String(500), nullable=True)

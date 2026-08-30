from __future__ import annotations

from sqlalchemy import CheckConstraint, Column, ForeignKey, Index, JSON, String

from apps.api.src.db.database import Base
from apps.api.src.db.types import UtcDateTime
from apps.api.src.models.booking_transition import REASON_CODES

_REASON_LIST = ", ".join(f"'{code}'" for code in REASON_CODES)


class BookingTransitionModel(Base):
    __tablename__ = "booking_transitions"
    __table_args__ = (
        CheckConstraint(f"reason_code IS NULL OR reason_code IN ({_REASON_LIST})", name="ck_booking_transitions_reason"),
        CheckConstraint(
            "actor_role IS NULL OR actor_role IN ('worker', 'operator', 'system')",
            name="ck_booking_transitions_actor_role",
        ),
        Index("ix_booking_transitions_booking", "booking_id", "occurred_at"),
        Index("ix_booking_transitions_state_occurred", "to_state", "occurred_at"),
    )

    transition_id = Column(String, primary_key=True)
    booking_id = Column(String, ForeignKey("bookings.booking_id", ondelete="CASCADE"), nullable=False)
    from_state = Column(String(30), nullable=True)
    to_state = Column(String(30), nullable=False)
    occurred_at = Column(UtcDateTime(), nullable=False)
    actor_user_id = Column(String, nullable=True)
    actor_role = Column(String(20), nullable=True)
    reason_code = Column(String(40), nullable=True)
    reason_note = Column(String(500), nullable=True)
    context = Column(JSON, nullable=False, default=dict)

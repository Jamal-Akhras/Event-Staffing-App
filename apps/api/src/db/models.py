from __future__ import annotations

from sqlalchemy import Column, DateTime, Enum, String

from apps.api.src.db.database import Base
from packages.domain.src.booking_state import BookingState


class BookingModel(Base):
    __tablename__ = "bookings"

    booking_id = Column(String, primary_key=True)
    shift_id = Column(String, nullable=False)
    worker_id = Column(String, nullable=False)
    operator_id = Column(String, nullable=False)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    state = Column(Enum(BookingState), nullable=False, default=BookingState.REQUESTED)

    created_at = Column(DateTime, nullable=True)
    confirmed_at = Column(DateTime, nullable=True)
    checked_in_at = Column(DateTime, nullable=True)
    checked_out_at = Column(DateTime, nullable=True)
    approved_at = Column(DateTime, nullable=True)
    paid_at = Column(DateTime, nullable=True)
    cancelled_at = Column(DateTime, nullable=True)
    no_show_at = Column(DateTime, nullable=True)

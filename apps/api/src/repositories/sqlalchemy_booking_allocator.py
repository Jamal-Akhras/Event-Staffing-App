from __future__ import annotations

from datetime import datetime

from sqlalchemy import select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from apps.api.src.db.models import BookingModel, ShiftModel
from apps.api.src.repositories.booking_allocator import (
    LIVE_STATES,
    AllocatedBooking,
    AllocationTargetMissingError,
    OverlappingBookingError,
    ShiftFullError,
    WorkerAlreadyBookedError,
)
from apps.api.src.repositories.sqlalchemy_application_decision_repository import (
    _booking_to_domain,
    _booking_to_model,
    _shift_to_domain,
)
from packages.domain.src.booking import Booking
from packages.domain.src.booking_state import BookingState


class SqlAlchemyBookingAllocator:
    def __init__(self, session: Session) -> None:
        self._session = session

    def allocate(
        self,
        shift_id: str,
        worker_id: str,
        now: datetime,
        booking_id: str,
        attendance_mode: str = "pin",
        allocation_source: str | None = None,
    ) -> AllocatedBooking:
        self._serialize_on_worker(worker_id)

        shift_model = self._session.execute(
            select(ShiftModel).where(ShiftModel.shift_id == shift_id).with_for_update()
        ).scalar_one_or_none()
        if shift_model is None:
            raise AllocationTargetMissingError(f"Shift {shift_id} was not found.")
        if shift_model.workers_filled >= shift_model.workers_needed:
            raise ShiftFullError("Shift is already fully staffed.")

        clash = self._session.execute(
            select(BookingModel.shift_id)
            .where(
                BookingModel.worker_id == worker_id,
                BookingModel.state.in_(LIVE_STATES),
                BookingModel.shift_id != shift_id,
                BookingModel.start_time < shift_model.end_time,
                BookingModel.end_time > shift_model.start_time,
            )
            .limit(1)
        ).scalar_one_or_none()
        if clash is not None:
            raise OverlappingBookingError(clash)

        booking = Booking(
            booking_id=booking_id,
            shift_id=shift_id,
            worker_id=worker_id,
            operator_id=shift_model.operator_id,
            start_time=shift_model.start_time,
            end_time=shift_model.end_time,
            created_at=now,
            attendance_mode=attendance_mode,
            allocation_source=allocation_source or shift_model.origin,
        ).transition_to(BookingState.CONFIRMED, now)

        try:
            with self._session.begin_nested():
                booking_model = _booking_to_model(booking)
                self._session.add(booking_model)
                self._session.flush()
        except IntegrityError as exc:
            raise WorkerAlreadyBookedError("Worker already has a booking on this shift.") from exc

        shift_model.workers_filled = shift_model.workers_filled + 1
        if shift_model.workers_filled >= shift_model.workers_needed:
            shift_model.status = "filled"
        self._session.flush()

        return AllocatedBooking(
            booking=_booking_to_domain(booking_model),
            shift=_shift_to_domain(shift_model),
        )

    def check_availability(
        self, worker_id: str, start_time: datetime, end_time: datetime, ignore_shift_id: str
    ) -> None:
        self._serialize_on_worker(worker_id)
        clash = self._session.execute(
            select(BookingModel.shift_id)
            .where(
                BookingModel.worker_id == worker_id,
                BookingModel.state.in_(LIVE_STATES),
                BookingModel.shift_id != ignore_shift_id,
                BookingModel.start_time < end_time,
                BookingModel.end_time > start_time,
            )
            .limit(1)
        ).scalar_one_or_none()
        if clash is not None:
            raise OverlappingBookingError(clash)

    def _serialize_on_worker(self, worker_id: str) -> None:
        if self._session.get_bind().dialect.name == "postgresql":
            self._session.execute(
                text("SELECT pg_advisory_xact_lock(hashtext(:worker_id))"),
                {"worker_id": worker_id},
            )

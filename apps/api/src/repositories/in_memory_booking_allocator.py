from __future__ import annotations

import threading
from dataclasses import replace
from datetime import datetime

from apps.api.src.repositories.booking_allocator import (
    LIVE_STATES,
    AllocatedBooking,
    AllocationTargetMissingError,
    OverlappingBookingError,
    ShiftFullError,
    WorkerAlreadyBookedError,
)
from apps.api.src.repositories.booking_repository import BookingRepository
from apps.api.src.repositories.shift_repository import ShiftRepository
from packages.domain.src.booking import Booking
from packages.domain.src.booking_state import BookingState

_ALLOCATOR_LOCK = threading.Lock()


class InMemoryBookingAllocator:
    def __init__(self, bookings: BookingRepository, shifts: ShiftRepository) -> None:
        self._bookings = bookings
        self._shifts = shifts

    def check_availability(
        self, worker_id: str, start_time: datetime, end_time: datetime, ignore_shift_id: str
    ) -> None:
        with _ALLOCATOR_LOCK:
            for existing in self._bookings.list_by_worker(worker_id):
                if (
                    existing.state in LIVE_STATES
                    and existing.shift_id != ignore_shift_id
                    and existing.start_time < end_time
                    and existing.end_time > start_time
                ):
                    raise OverlappingBookingError(existing.shift_id)

    def allocate(
        self,
        shift_id: str,
        worker_id: str,
        now: datetime,
        booking_id: str,
        attendance_mode: str = "pin",
    ) -> AllocatedBooking:
        with _ALLOCATOR_LOCK:
            shift = self._shifts.get(shift_id)
            if shift is None:
                raise AllocationTargetMissingError(f"Shift {shift_id} was not found.")
            if shift.workers_filled >= shift.workers_needed:
                raise ShiftFullError("Shift is already fully staffed.")

            if any(
                existing.worker_id == worker_id
                for existing in self._bookings.list_by_shift(shift_id)
            ):
                raise WorkerAlreadyBookedError("Worker already has a booking on this shift.")

            for existing in self._bookings.list_by_worker(worker_id):
                if (
                    existing.state in LIVE_STATES
                    and existing.shift_id != shift_id
                    and existing.start_time < shift.end_time
                    and existing.end_time > shift.start_time
                ):
                    raise OverlappingBookingError(existing.shift_id)

            booking = Booking(
                booking_id=booking_id,
                shift_id=shift_id,
                worker_id=worker_id,
                operator_id=shift.operator_id,
                start_time=shift.start_time,
                end_time=shift.end_time,
                created_at=now,
                attendance_mode=attendance_mode,
            ).transition_to(BookingState.CONFIRMED, now)
            self._bookings.save(booking)

            workers_filled = shift.workers_filled + 1
            status = "filled" if workers_filled >= shift.workers_needed else shift.status
            updated = self._shifts.save(
                replace(shift, workers_filled=workers_filled, status=status, updated_at=now)
            )
            return AllocatedBooking(booking=booking, shift=updated)

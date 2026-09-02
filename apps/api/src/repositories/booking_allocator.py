from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol

from apps.api.src.models.shift import Shift
from packages.domain.src.booking import Booking
from packages.domain.src.booking_state import BookingState

LIVE_STATES = (
    BookingState.CONFIRMED,
    BookingState.CHECKED_IN,
    BookingState.CHECKED_OUT,
    BookingState.APPROVED,
    BookingState.PAID,
)


class AllocationError(Exception):
    pass


class AllocationTargetMissingError(AllocationError):
    pass


class ShiftFullError(AllocationError):
    pass


class WorkerAlreadyBookedError(AllocationError):
    pass


class OverlappingBookingError(AllocationError):
    def __init__(self, clashing_shift_id: str) -> None:
        super().__init__(f"Worker already has a booking overlapping shift {clashing_shift_id}.")
        self.clashing_shift_id = clashing_shift_id


@dataclass(frozen=True)
class AllocatedBooking:
    booking: Booking
    shift: Shift


class BookingAllocator(Protocol):
    def allocate(
        self,
        shift_id: str,
        worker_id: str,
        now: datetime,
        booking_id: str,
        attendance_mode: str = "pin",
    ) -> AllocatedBooking: ...

    def check_availability(
        self, worker_id: str, start_time: datetime, end_time: datetime, ignore_shift_id: str
    ) -> None: ...

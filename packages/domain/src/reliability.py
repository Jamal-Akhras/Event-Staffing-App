from __future__ import annotations

from typing import Iterable

from packages.domain.src.booking import Booking
from packages.domain.src.booking_state import BookingState

_COMPLETED = {BookingState.CHECKED_OUT, BookingState.APPROVED, BookingState.PAID}
_NEGATIVE = {BookingState.NO_SHOW, BookingState.CANCELLED_BY_WORKER}


def compute_reliability(bookings: Iterable[Booking]) -> float:
    completed = 0
    negative = 0
    for booking in bookings:
        if booking.state in _COMPLETED:
            completed += 1
        elif booking.state in _NEGATIVE:
            negative += 1
    total = completed + negative
    if total == 0:
        return 0.0
    return completed / total

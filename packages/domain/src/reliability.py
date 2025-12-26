from __future__ import annotations

from typing import Iterable

from packages.domain.src.booking import Booking
from packages.domain.src.booking_state import BookingState


def compute_reliability(bookings: Iterable[Booking]) -> float:
    completed = 0
    negative = 0

    for booking in bookings:
        if booking.state in {
            BookingState.CHECKED_OUT,
            BookingState.APPROVED,
            BookingState.PAID,
        }:
            completed += 1
            continue
        if booking.state == BookingState.NO_SHOW:
            negative += 1
            continue
        if booking.state == BookingState.CANCELLED_BY_WORKER:
            negative += 1

    total = completed + negative
    if total == 0:
        return 0.0
    return completed / total

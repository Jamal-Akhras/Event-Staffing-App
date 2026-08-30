from __future__ import annotations

from datetime import datetime
from decimal import ROUND_HALF_UP, Decimal

from packages.domain.src.booking import Booking

PENNY = Decimal("0.01")


def completed_at(booking: Booking) -> datetime:
    return booking.approved_at or booking.checked_out_at or booking.end_time


def worked_hours(booking: Booking) -> Decimal:
    if booking.checked_in_at and booking.checked_out_at:
        start, end = booking.checked_in_at, booking.checked_out_at
    else:
        start, end = booking.start_time, booking.end_time
    return (Decimal((end - start).total_seconds()) / Decimal(3600)).quantize(PENNY, rounding=ROUND_HALF_UP)


def money(value: Decimal) -> Decimal:
    return value.quantize(PENNY, rounding=ROUND_HALF_UP)

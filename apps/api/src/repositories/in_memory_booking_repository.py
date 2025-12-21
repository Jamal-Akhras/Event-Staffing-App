from __future__ import annotations

from typing import Dict

from packages.domain.src.booking import Booking


class InMemoryBookingRepository:
    def __init__(self) -> None:
        self._bookings: Dict[str, Booking] = {}

    def get(self, booking_id: str) -> Booking | None:
        return self._bookings.get(booking_id)

    def save(self, booking: Booking) -> Booking:
        self._bookings[booking.booking_id] = booking
        return booking

    def list_recent(self, limit: int = 25) -> list[Booking]:
        bookings = list(self._bookings.values())
        bookings.sort(key=lambda item: item.created_at or item.start_time, reverse=True)
        return bookings[:limit]

    def clear(self) -> None:
        self._bookings.clear()

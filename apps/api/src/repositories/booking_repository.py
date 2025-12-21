from __future__ import annotations

from typing import Protocol

from packages.domain.src.booking import Booking


class BookingRepository(Protocol):
    def get(self, booking_id: str) -> Booking | None:
        raise NotImplementedError

    def save(self, booking: Booking) -> Booking:
        raise NotImplementedError

    def list_recent(self, limit: int = 25) -> list[Booking]:
        raise NotImplementedError

from __future__ import annotations

from typing import Protocol

from packages.domain.src.booking import Booking
from packages.domain.src.booking_state import BookingState


class BookingRepository(Protocol):
    def get(self, booking_id: str) -> Booking | None:
        raise NotImplementedError

    def save(self, booking: Booking) -> Booking:
        raise NotImplementedError

    def list_recent(self, limit: int = 25) -> list[Booking]:
        raise NotImplementedError

    def list_by_worker(self, worker_id: str) -> list[Booking]:
        raise NotImplementedError

    def list_by_state(self, state: BookingState) -> list[Booking]:
        raise NotImplementedError

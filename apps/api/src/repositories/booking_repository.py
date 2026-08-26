from __future__ import annotations

from typing import Protocol

from packages.domain.src.booking import Booking
from packages.domain.src.booking_state import BookingState


class BookingRepository(Protocol):
    def get(self, booking_id: str) -> Booking | None:
        ...

    def save(self, booking: Booking) -> Booking:
        ...

    def list_recent(self, limit: int = 25) -> list[Booking]:
        ...

    def list_by_worker(
        self,
        worker_id: str,
        limit: int | None = None,
        operator_id: str | None = None,
    ) -> list[Booking]:
        ...

    def list_by_operator(
        self,
        operator_id: str,
        limit: int = 25,
        worker_id: str | None = None,
    ) -> list[Booking]:
        ...

    def list_for_account(
        self,
        account_id: str,
        limit: int = 25,
        worker_id: str | None = None,
    ) -> list[Booking]:
        ...

    def list_by_state(self, state: BookingState) -> list[Booking]:
        ...

    def list_by_shift(self, shift_id: str, for_update: bool = False) -> list[Booking]:
        ...

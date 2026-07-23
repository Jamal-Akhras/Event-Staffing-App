from __future__ import annotations

from typing import Dict

from apps.api.src.repositories.shift_repository import ShiftRepository
from packages.domain.src.booking import Booking
from packages.domain.src.booking_state import BookingState


class InMemoryBookingRepository:
    def __init__(self) -> None:
        self._bookings: Dict[str, Booking] = {}
        self._shift_repo: ShiftRepository | None = None

    def attach_shift_repo(self, shift_repo: ShiftRepository) -> None:
        self._shift_repo = shift_repo

    def get(self, booking_id: str) -> Booking | None:
        return self._bookings.get(booking_id)

    def save(self, booking: Booking) -> Booking:
        self._bookings[booking.booking_id] = booking
        return booking

    def list_recent(self, limit: int = 25) -> list[Booking]:
        bookings = list(self._bookings.values())
        bookings.sort(key=lambda item: item.created_at or item.start_time, reverse=True)
        return bookings[:limit]

    def list_by_worker(
        self,
        worker_id: str,
        limit: int | None = None,
        operator_id: str | None = None,
    ) -> list[Booking]:
        return self._list(limit, worker_id=worker_id, operator_id=operator_id)

    def list_by_operator(
        self,
        operator_id: str,
        limit: int = 25,
        worker_id: str | None = None,
    ) -> list[Booking]:
        return self._list(limit, worker_id=worker_id, operator_id=operator_id)

    def list_for_account(
        self,
        account_id: str,
        limit: int = 25,
        worker_id: str | None = None,
    ) -> list[Booking]:
        if self._shift_repo is None:
            raise RuntimeError("InMemoryBookingRepository requires a shift repo to list by account.")
        account_shift_ids = {shift.shift_id for shift in self._shift_repo.list_for_account(account_id, limit=10_000)}
        items = [item for item in self._bookings.values() if item.shift_id in account_shift_ids]
        if worker_id:
            items = [item for item in items if item.worker_id == worker_id]
        items.sort(key=lambda item: item.created_at or item.start_time, reverse=True)
        return items[:limit]

    def list_by_state(self, state: BookingState) -> list[Booking]:
        return [booking for booking in self._bookings.values() if booking.state == state]

    def clear(self) -> None:
        self._bookings.clear()

    def _list(
        self,
        limit: int | None,
        worker_id: str | None = None,
        operator_id: str | None = None,
    ) -> list[Booking]:
        items = list(self._bookings.values())
        if worker_id:
            items = [item for item in items if item.worker_id == worker_id]
        if operator_id:
            items = [item for item in items if item.operator_id == operator_id]
        items.sort(key=lambda item: item.created_at or item.start_time, reverse=True)
        return items if limit is None else items[:limit]

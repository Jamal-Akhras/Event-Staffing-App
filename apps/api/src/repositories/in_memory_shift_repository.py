from __future__ import annotations

from typing import Dict

from apps.api.src.models.shift import Shift
from apps.api.src.repositories.booking_repository import BookingRepository


class InMemoryShiftRepository:
    def __init__(self, booking_repo: BookingRepository | None = None) -> None:
        self._shifts: Dict[str, Shift] = {}
        self._booking_repo = booking_repo

    def get(self, shift_id: str) -> Shift | None:
        return self._shifts.get(shift_id)

    def save(self, shift: Shift) -> Shift:
        self._shifts[shift.shift_id] = shift
        return shift

    def list_recent(self, limit: int = 50) -> list[Shift]:
        items = list(self._shifts.values())
        items.sort(key=lambda item: item.created_at, reverse=True)
        return items[:limit]

    def list_for_account(self, account_id: str, limit: int = 50) -> list[Shift]:
        items = [s for s in self._shifts.values() if s.account_id == account_id]
        items.sort(key=lambda item: item.created_at, reverse=True)
        return items[:limit]

    def list_by_worker(self, worker_id: str, limit: int = 50) -> list[Shift]:
        if self._booking_repo is None:
            raise RuntimeError("InMemoryShiftRepository requires a booking repo to list shifts by worker.")
        shift_ids = {booking.shift_id for booking in self._booking_repo.list_by_worker(worker_id, limit)}
        items = [shift for shift in self._shifts.values() if shift.shift_id in shift_ids]
        items.sort(key=lambda item: item.created_at, reverse=True)
        return items[:limit]

    def clear(self) -> None:
        self._shifts.clear()

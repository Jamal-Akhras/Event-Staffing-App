from __future__ import annotations

from datetime import datetime
from typing import Dict

from apps.api.src.models.shift import Shift
from apps.api.src.repositories.booking_repository import BookingRepository


class InMemoryShiftRepository:
    def __init__(self, booking_repo: BookingRepository | None = None) -> None:
        self._shifts: Dict[str, Shift] = {}
        self._booking_repo = booking_repo

    def get(self, shift_id: str) -> Shift | None:
        return self._shifts.get(shift_id)

    def get_for_update(self, shift_id: str) -> Shift | None:
        return self.get(shift_id)

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

    def list_in_range(self, account_id: str, start: datetime, end: datetime) -> list[Shift]:
        items = [
            shift
            for shift in self._shifts.values()
            if shift.account_id == account_id and start <= shift.start_time < end
        ]
        items.sort(key=lambda item: item.start_time)
        return items

    def list_by_ids(self, shift_ids: list[str]) -> list[Shift]:
        return [self._shifts[shift_id] for shift_id in shift_ids if shift_id in self._shifts]

    def list_due_for_escalation(self, now: datetime) -> list[Shift]:
        due = [
            shift
            for shift in self._shifts.values()
            if shift.status == "open"
            and shift.rota_state == "published"
            and not shift.needs_attention
            and shift.start_time > now
            and shift.workers_filled < shift.workers_needed
            and _rung_is_due(shift, now)
        ]
        return sorted(due, key=lambda shift: shift.start_time)

    def clear(self) -> None:
        self._shifts.clear()


def _rung_is_due(shift: Shift, now: datetime) -> bool:
    if shift.origin == "assigned":
        stamps = (shift.offer_team_at, shift.offer_pool_at, shift.publish_market_at)
    elif shift.origin == "team":
        stamps = (shift.offer_pool_at, shift.publish_market_at)
    elif shift.origin == "pool":
        stamps = (shift.publish_market_at,)
    else:
        return False
    next_stamp = next((stamp for stamp in stamps if stamp is not None), None)
    return next_stamp is not None and next_stamp <= now

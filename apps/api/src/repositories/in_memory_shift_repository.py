from __future__ import annotations

from typing import Dict

from apps.api.src.models.shift import Shift


class InMemoryShiftRepository:
    def __init__(self) -> None:
        self._shifts: Dict[str, Shift] = {}

    def get(self, shift_id: str) -> Shift | None:
        return self._shifts.get(shift_id)

    def save(self, shift: Shift) -> Shift:
        self._shifts[shift.shift_id] = shift
        return shift

    def list_recent(self, limit: int = 50) -> list[Shift]:
        items = list(self._shifts.values())
        items.sort(key=lambda item: item.created_at, reverse=True)
        return items[:limit]

    def clear(self) -> None:
        self._shifts.clear()

from __future__ import annotations

from datetime import datetime
from typing import Protocol

from apps.api.src.models.shift import Shift


class ShiftRepository(Protocol):
    def get(self, shift_id: str) -> Shift | None:
        ...

    def get_for_update(self, shift_id: str) -> Shift | None:
        ...

    def save(self, shift: Shift) -> Shift:
        ...

    def list_recent(self, limit: int = 50) -> list[Shift]:
        ...

    def list_for_account(self, account_id: str, limit: int = 50) -> list[Shift]:
        ...

    def list_by_worker(self, worker_id: str, limit: int = 50) -> list[Shift]:
        ...

    def list_in_range(self, account_id: str, start: datetime, end: datetime) -> list[Shift]:
        ...

    def list_by_ids(self, shift_ids: list[str]) -> list[Shift]:
        ...

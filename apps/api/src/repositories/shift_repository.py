from __future__ import annotations

from typing import Protocol

from apps.api.src.models.shift import Shift


class ShiftRepository(Protocol):
    def get(self, shift_id: str) -> Shift | None:
        raise NotImplementedError

    def get_for_update(self, shift_id: str) -> Shift | None:
        raise NotImplementedError

    def save(self, shift: Shift) -> Shift:
        raise NotImplementedError

    def list_recent(self, limit: int = 50) -> list[Shift]:
        raise NotImplementedError

    def list_for_account(self, account_id: str, limit: int = 50) -> list[Shift]:
        raise NotImplementedError

    def list_by_worker(self, worker_id: str, limit: int = 50) -> list[Shift]:
        raise NotImplementedError

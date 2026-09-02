from __future__ import annotations

from typing import Protocol

from apps.api.src.models.worker_profile import WorkerProfile


class WorkerProfileRepository(Protocol):
    def get(self, worker_id: str) -> WorkerProfile | None:
        ...

    def save(self, profile: WorkerProfile) -> WorkerProfile:
        ...

    def list_all(self) -> list[WorkerProfile]:
        ...

    def list_by_ids(self, worker_ids: list[str]) -> list[WorkerProfile]:
        ...

    def list_for_account(self, account_id: str) -> list[WorkerProfile]:
        ...

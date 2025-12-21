from __future__ import annotations

from typing import Protocol

from apps.api.src.models.worker_profile import WorkerProfile


class WorkerProfileRepository(Protocol):
    def get(self, worker_id: str) -> WorkerProfile | None:
        raise NotImplementedError

    def save(self, profile: WorkerProfile) -> WorkerProfile:
        raise NotImplementedError

from __future__ import annotations

from typing import Dict

from apps.api.src.models.worker_profile import WorkerProfile


class InMemoryWorkerProfileRepository:
    def __init__(self) -> None:
        self._profiles: Dict[str, WorkerProfile] = {}

    def get(self, worker_id: str) -> WorkerProfile | None:
        return self._profiles.get(worker_id)

    def save(self, profile: WorkerProfile) -> WorkerProfile:
        self._profiles[profile.worker_id] = profile
        return profile

    def list_all(self) -> list[WorkerProfile]:
        return list(self._profiles.values())

    def list_by_ids(self, worker_ids: list[str]) -> list[WorkerProfile]:
        return [self._profiles[worker_id] for worker_id in worker_ids if worker_id in self._profiles]

    def clear(self) -> None:
        self._profiles.clear()

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

    def clear(self) -> None:
        self._profiles.clear()

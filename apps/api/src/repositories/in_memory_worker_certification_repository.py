from __future__ import annotations

from datetime import datetime

from apps.api.src.models.worker_certification import WorkerCertification


class InMemoryWorkerCertificationRepository:
    def __init__(self) -> None:
        self._items: dict[tuple[str, str], WorkerCertification] = {}

    def clear(self) -> None:
        self._items.clear()

    def save(self, certification: WorkerCertification) -> WorkerCertification:
        self._items[(certification.worker_id, certification.name)] = certification
        return certification

    def get(self, worker_id: str, name: str) -> WorkerCertification | None:
        return self._items.get((worker_id, name))

    def list_for_worker(self, worker_id: str) -> list[WorkerCertification]:
        rows = [item for key, item in self._items.items() if key[0] == worker_id]
        return sorted(rows, key=lambda item: item.expires_at)

    def delete(self, worker_id: str, name: str) -> bool:
        return self._items.pop((worker_id, name), None) is not None

    def list_expiring_between(
        self, start: datetime, end: datetime
    ) -> list[WorkerCertification]:
        rows = [item for item in self._items.values() if start <= item.expires_at < end]
        return sorted(rows, key=lambda item: item.expires_at)

from __future__ import annotations

from datetime import datetime
from typing import Protocol

from apps.api.src.models.worker_certification import WorkerCertification


class WorkerCertificationRepository(Protocol):
    def save(self, certification: WorkerCertification) -> WorkerCertification:
        ...

    def get(self, worker_id: str, name: str) -> WorkerCertification | None:
        ...

    def list_for_worker(self, worker_id: str) -> list[WorkerCertification]:
        ...

    def delete(self, worker_id: str, name: str) -> bool:
        ...

    def list_expiring_between(
        self, start: datetime, end: datetime
    ) -> list[WorkerCertification]:
        ...

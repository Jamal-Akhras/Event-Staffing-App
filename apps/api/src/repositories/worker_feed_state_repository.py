from __future__ import annotations

from typing import Protocol

from apps.api.src.models.worker_feed_state import WorkerFeedState


class WorkerFeedStateRepository(Protocol):
    def list_for_worker(self, worker_id: str) -> list[WorkerFeedState]:
        raise NotImplementedError

    def get(self, worker_id: str, shift_id: str) -> WorkerFeedState | None:
        raise NotImplementedError

    def save(self, state: WorkerFeedState) -> WorkerFeedState:
        raise NotImplementedError

    def delete(self, worker_id: str, shift_id: str) -> bool:
        raise NotImplementedError

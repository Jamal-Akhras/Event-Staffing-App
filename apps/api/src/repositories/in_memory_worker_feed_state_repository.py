from __future__ import annotations

from apps.api.src.models.worker_feed_state import WorkerFeedState


class InMemoryWorkerFeedStateRepository:
    def __init__(self) -> None:
        self._items: dict[tuple[str, str], WorkerFeedState] = {}

    def list_for_worker(self, worker_id: str) -> list[WorkerFeedState]:
        items = [item for item in self._items.values() if item.worker_id == worker_id]
        items.sort(key=lambda item: item.updated_at, reverse=True)
        return items

    def get(self, worker_id: str, shift_id: str) -> WorkerFeedState | None:
        return self._items.get((worker_id, shift_id))

    def save(self, state: WorkerFeedState) -> WorkerFeedState:
        self._items[(state.worker_id, state.shift_id)] = state
        return state

    def delete(self, worker_id: str, shift_id: str) -> bool:
        key = (worker_id, shift_id)
        if key not in self._items:
            return False
        del self._items[key]
        return True

    def clear(self) -> None:
        self._items.clear()

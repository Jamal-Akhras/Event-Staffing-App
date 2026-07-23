from __future__ import annotations

from apps.api.src.helpers import _now_or
from apps.api.src.models.worker_feed_state import WorkerFeedState
from apps.api.src.repositories.shift_repository import ShiftRepository
from apps.api.src.repositories.worker_feed_state_repository import WorkerFeedStateRepository
from apps.api.src.schemas import WorkerFeedStateUpdateRequest
from apps.api.src.services.errors import NotFoundError, ValidationError


class WorkerFeedService:
    def __init__(
        self,
        repo: WorkerFeedStateRepository,
        shift_repo: ShiftRepository,
    ) -> None:
        self._repo = repo
        self._shifts = shift_repo

    def list_state(self, worker_id: str) -> list[WorkerFeedState]:
        return self._repo.list_for_worker(worker_id)

    def save_state(
        self,
        worker_id: str,
        shift_id: str,
        request: WorkerFeedStateUpdateRequest,
    ) -> WorkerFeedState:
        if request.action != "passed":
            raise ValidationError("Unsupported feed action.")
        if self._shifts.get(shift_id) is None:
            raise NotFoundError("Shift not found.")
        now = _now_or(request.now)
        existing = self._repo.get(worker_id, shift_id)
        created_at = now if existing is None else existing.created_at
        return self._repo.save(
            WorkerFeedState(
                worker_id=worker_id,
                shift_id=shift_id,
                action=request.action,
                created_at=created_at,
                updated_at=now,
            )
        )

    def delete_state(self, worker_id: str, shift_id: str) -> bool:
        return self._repo.delete(worker_id, shift_id)

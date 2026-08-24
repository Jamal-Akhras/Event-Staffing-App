from __future__ import annotations

from sqlalchemy import desc
from sqlalchemy.orm import Session

from apps.api.src.db.models import WorkerFeedStateModel
from apps.api.src.models.worker_feed_state import WorkerFeedState


class SqlAlchemyWorkerFeedStateRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def list_for_worker(self, worker_id: str) -> list[WorkerFeedState]:
        rows = (
            self._session.query(WorkerFeedStateModel)
            .filter(WorkerFeedStateModel.worker_id == worker_id)
            .order_by(desc(WorkerFeedStateModel.updated_at))
            .all()
        )
        return [_to_domain(row) for row in rows]

    def get(self, worker_id: str, shift_id: str) -> WorkerFeedState | None:
        model = self._session.get(WorkerFeedStateModel, (worker_id, shift_id))
        if model is None:
            return None
        return _to_domain(model)

    def save(self, state: WorkerFeedState) -> WorkerFeedState:
        model = self._session.get(WorkerFeedStateModel, (state.worker_id, state.shift_id))
        if model is None:
            model = WorkerFeedStateModel(worker_id=state.worker_id, shift_id=state.shift_id)
            self._session.add(model)
        model.action = state.action
        model.created_at = state.created_at
        model.updated_at = state.updated_at
        self._session.flush()
        return state

    def delete(self, worker_id: str, shift_id: str) -> bool:
        model = self._session.get(WorkerFeedStateModel, (worker_id, shift_id))
        if model is None:
            return False
        self._session.delete(model)
        self._session.flush()
        return True


def _to_domain(model: WorkerFeedStateModel) -> WorkerFeedState:
    return WorkerFeedState(
        worker_id=model.worker_id,
        shift_id=model.shift_id,
        action=model.action,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )

from __future__ import annotations

from dataclasses import fields
from datetime import datetime

from sqlalchemy.orm import Session

from apps.api.src.db.certification_models import WorkerCertificationModel
from apps.api.src.models.worker_certification import WorkerCertification

_FIELDS = tuple(field.name for field in fields(WorkerCertification))


class SqlAlchemyWorkerCertificationRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def save(self, certification: WorkerCertification) -> WorkerCertification:
        model = self._model(certification.worker_id, certification.name)
        if model is None:
            model = WorkerCertificationModel(certification_id=certification.certification_id)
            self._session.add(model)
        for name in _FIELDS:
            setattr(model, name, getattr(certification, name))
        self._session.flush()
        return certification

    def get(self, worker_id: str, name: str) -> WorkerCertification | None:
        model = self._model(worker_id, name)
        return _to_domain(model) if model is not None else None

    def list_for_worker(self, worker_id: str) -> list[WorkerCertification]:
        rows = (
            self._session.query(WorkerCertificationModel)
            .filter(WorkerCertificationModel.worker_id == worker_id)
            .order_by(WorkerCertificationModel.expires_at)
            .all()
        )
        return [_to_domain(row) for row in rows]

    def delete(self, worker_id: str, name: str) -> bool:
        model = self._model(worker_id, name)
        if model is None:
            return False
        self._session.delete(model)
        self._session.flush()
        return True

    def list_expiring_between(
        self, start: datetime, end: datetime
    ) -> list[WorkerCertification]:
        rows = (
            self._session.query(WorkerCertificationModel)
            .filter(WorkerCertificationModel.expires_at >= start)
            .filter(WorkerCertificationModel.expires_at < end)
            .order_by(WorkerCertificationModel.expires_at)
            .all()
        )
        return [_to_domain(row) for row in rows]

    def _model(self, worker_id: str, name: str) -> WorkerCertificationModel | None:
        return (
            self._session.query(WorkerCertificationModel)
            .filter(WorkerCertificationModel.worker_id == worker_id)
            .filter(WorkerCertificationModel.name == name)
            .one_or_none()
        )


def _to_domain(model: WorkerCertificationModel) -> WorkerCertification:
    return WorkerCertification(**{name: getattr(model, name) for name in _FIELDS})

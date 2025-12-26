from __future__ import annotations

from sqlalchemy import desc
from sqlalchemy.orm import Session

from apps.api.src.db.models import ApplicationModel
from apps.api.src.models.application import Application


class SqlAlchemyApplicationRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def get(self, application_id: str) -> Application | None:
        model = self._session.get(ApplicationModel, application_id)
        if model is None:
            return None
        return _to_domain(model)

    def save(self, application: Application) -> Application:
        model = self._session.get(ApplicationModel, application.application_id)
        if model is None:
            model = ApplicationModel(application_id=application.application_id)
            self._session.add(model)
        _apply_domain(model, application)
        self._session.commit()
        return application

    def list_recent(self, limit: int = 50) -> list[Application]:
        rows = (
            self._session.query(ApplicationModel)
            .order_by(desc(ApplicationModel.created_at))
            .limit(limit)
            .all()
        )
        return [_to_domain(row) for row in rows]


def _to_domain(model: ApplicationModel) -> Application:
    return Application(
        application_id=model.application_id,
        shift_id=model.shift_id,
        worker_id=model.worker_id,
        operator_id=model.operator_id,
        start_time=model.start_time,
        end_time=model.end_time,
        message=model.message,
        booking_id=model.booking_id,
        status=model.status,
        created_at=model.created_at,
        decided_at=model.decided_at,
    )


def _apply_domain(model: ApplicationModel, application: Application) -> None:
    model.shift_id = application.shift_id
    model.worker_id = application.worker_id
    model.operator_id = application.operator_id
    model.start_time = application.start_time
    model.end_time = application.end_time
    model.message = application.message
    model.booking_id = application.booking_id
    model.status = application.status
    model.created_at = application.created_at
    model.decided_at = application.decided_at

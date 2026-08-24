from __future__ import annotations

from sqlalchemy.orm import Session

from apps.api.src.db.models import ApplicationMessageHistoryModel
from apps.api.src.models.application_message_history import ApplicationMessageHistory


class SqlAlchemyApplicationMessageHistoryRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def save(self, history: ApplicationMessageHistory) -> ApplicationMessageHistory:
        model = ApplicationMessageHistoryModel(
            history_id=history.history_id,
            application_id=history.application_id,
            message=history.message,
            edited_at=history.edited_at,
        )
        self._session.add(model)
        self._session.flush()
        return history

    def list_by_application(self, application_id: str) -> list[ApplicationMessageHistory]:
        rows = (
            self._session.query(ApplicationMessageHistoryModel)
            .filter(ApplicationMessageHistoryModel.application_id == application_id)
            .order_by(ApplicationMessageHistoryModel.edited_at.asc())
            .all()
        )
        return [_to_domain(row) for row in rows]


def _to_domain(model: ApplicationMessageHistoryModel) -> ApplicationMessageHistory:
    return ApplicationMessageHistory(
        history_id=model.history_id,
        application_id=model.application_id,
        message=model.message,
        edited_at=model.edited_at,
    )

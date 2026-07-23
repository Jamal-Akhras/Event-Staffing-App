from __future__ import annotations

from sqlalchemy.orm import Session

from apps.api.src.db.models import NotificationModel
from apps.api.src.models.notification import Notification


class SqlAlchemyNotificationRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def list_for_worker(self, worker_id: str, limit: int = 50) -> list[Notification]:
        rows = (
            self._session.query(NotificationModel)
            .filter(NotificationModel.worker_id == worker_id)
            .order_by(NotificationModel.created_at.desc())
            .limit(limit)
            .all()
        )
        return [_to_domain(r) for r in rows]

    def save(self, notification: Notification) -> Notification:
        row = self._session.get(NotificationModel, notification.notification_id)
        if row is None:
            row = NotificationModel()
            self._session.add(row)
        row.notification_id = notification.notification_id
        row.worker_id = notification.worker_id
        row.type = notification.type
        row.title = notification.title
        row.body = notification.body
        row.shift_id = notification.shift_id
        row.read = notification.read
        row.created_at = notification.created_at
        self._session.commit()
        return notification

    def mark_all_read(self, worker_id: str) -> int:
        count = (
            self._session.query(NotificationModel)
            .filter(NotificationModel.worker_id == worker_id, NotificationModel.read == False)
            .update({"read": True})
        )
        self._session.commit()
        return count


def _to_domain(row: NotificationModel) -> Notification:
    return Notification(
        notification_id=row.notification_id,
        worker_id=row.worker_id,
        type=row.type,
        title=row.title,
        body=row.body,
        shift_id=row.shift_id,
        read=row.read,
        created_at=row.created_at,
    )

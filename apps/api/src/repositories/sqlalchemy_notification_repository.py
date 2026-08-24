from __future__ import annotations

from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from apps.api.src.db.models import NotificationModel
from apps.api.src.models.notification import Notification


class SqlAlchemyNotificationRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def list_for_worker(self, worker_id: str, limit: int = 50) -> list[Notification]:
        return self.list_for_recipient("worker", worker_id, limit)

    def list_for_recipient(
        self,
        recipient_kind: str,
        recipient_id: str,
        limit: int,
        cursor: tuple[object, str] | None = None,
    ) -> list[Notification]:
        query = self._session.query(NotificationModel).filter(
            self._recipient_filter(recipient_kind, recipient_id)
        )
        if cursor is not None:
            created_at, notification_id = cursor
            query = query.filter(
                or_(
                    NotificationModel.created_at < created_at,
                    and_(
                        NotificationModel.created_at == created_at,
                        NotificationModel.notification_id < notification_id,
                    ),
                )
            )
        rows = (
            query.order_by(NotificationModel.created_at.desc(), NotificationModel.notification_id.desc())
            .limit(limit)
            .all()
        )
        return [_to_domain(r) for r in rows]

    def unread_count(self, recipient_kind: str, recipient_id: str) -> int:
        return (
            self._session.query(NotificationModel)
            .filter(self._recipient_filter(recipient_kind, recipient_id), NotificationModel.read == False)
            .count()
        )

    def mark_read(self, notification_id: str, recipient_kind: str, recipient_id: str) -> bool:
        count = (
            self._session.query(NotificationModel)
            .filter(
                NotificationModel.notification_id == notification_id,
                self._recipient_filter(recipient_kind, recipient_id),
            )
            .update({"read": True}, synchronize_session=False)
        )
        self._session.flush()
        return count == 1

    def save(self, notification: Notification) -> Notification:
        row = self._session.get(NotificationModel, notification.notification_id)
        if row is None:
            row = NotificationModel()
            self._session.add(row)
        row.notification_id = notification.notification_id
        row.worker_id = notification.worker_id
        row.venue_id = notification.venue_id
        row.type = notification.type
        row.title = notification.title
        row.body = notification.body
        row.shift_id = notification.shift_id
        row.action_kind = notification.action_kind
        row.action_entity_id = notification.action_entity_id
        row.delivery_id = notification.delivery_id
        row.read = notification.read
        row.created_at = notification.created_at
        self._session.flush()
        return notification

    def mark_all_read(self, worker_id: str) -> int:
        return self.mark_all_read_for_recipient("worker", worker_id)

    def mark_all_read_for_recipient(self, recipient_kind: str, recipient_id: str) -> int:
        count = (
            self._session.query(NotificationModel)
            .filter(self._recipient_filter(recipient_kind, recipient_id), NotificationModel.read == False)
            .update({"read": True}, synchronize_session=False)
        )
        self._session.flush()
        return count

    @staticmethod
    def _recipient_filter(recipient_kind: str, recipient_id: str):
        if recipient_kind == "worker":
            return NotificationModel.worker_id == recipient_id
        if recipient_kind == "venue":
            return NotificationModel.venue_id == recipient_id
        raise ValueError(f"Unsupported notification recipient kind: {recipient_kind}")


def _to_domain(row: NotificationModel) -> Notification:
    return Notification(
        notification_id=row.notification_id,
        worker_id=row.worker_id,
        venue_id=row.venue_id,
        type=row.type,
        title=row.title,
        body=row.body,
        shift_id=row.shift_id,
        action_kind=row.action_kind,
        action_entity_id=row.action_entity_id,
        delivery_id=row.delivery_id,
        read=row.read,
        created_at=row.created_at,
    )

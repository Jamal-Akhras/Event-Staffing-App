from __future__ import annotations

from typing import Dict

from apps.api.src.models.notification import Notification


class InMemoryNotificationRepository:
    def __init__(self) -> None:
        self._notifications: Dict[str, Notification] = {}

    def list_for_worker(self, worker_id: str, limit: int = 50) -> list[Notification]:
        return self.list_for_recipient("worker", worker_id, limit)

    def list_for_recipient(
        self,
        recipient_kind: str,
        recipient_id: str,
        limit: int,
        cursor: tuple[object, str] | None = None,
    ) -> list[Notification]:
        field = "worker_id" if recipient_kind == "worker" else "venue_id"
        items = [n for n in self._notifications.values() if getattr(n, field) == recipient_id]
        items.sort(key=lambda n: (n.created_at, n.notification_id), reverse=True)
        if cursor is not None:
            created_at, notification_id = cursor
            items = [n for n in items if (n.created_at, n.notification_id) < (created_at, notification_id)]
        return items[:limit]

    def unread_count(self, recipient_kind: str, recipient_id: str) -> int:
        return sum(not item.read for item in self.list_for_recipient(recipient_kind, recipient_id, 10000))

    def mark_read(self, notification_id: str, recipient_kind: str, recipient_id: str) -> bool:
        notification = self._notifications.get(notification_id)
        field = "worker_id" if recipient_kind == "worker" else "venue_id"
        if notification is None or getattr(notification, field) != recipient_id:
            return False
        self._notifications[notification_id] = _mark_read(notification)
        return True

    def save(self, notification: Notification) -> Notification:
        self._notifications[notification.notification_id] = notification
        return notification

    def mark_all_read(self, worker_id: str) -> int:
        return self.mark_all_read_for_recipient("worker", worker_id)

    def mark_all_read_for_recipient(self, recipient_kind: str, recipient_id: str) -> int:
        count = 0
        for notification_id, notification in self._notifications.items():
            field = "worker_id" if recipient_kind == "worker" else "venue_id"
            if getattr(notification, field) == recipient_id and not notification.read:
                self._notifications[notification_id] = _mark_read(notification)
                count += 1
        return count

    def clear(self) -> None:
        self._notifications.clear()


def _mark_read(notification: Notification) -> Notification:
    from dataclasses import replace

    return replace(notification, read=True)

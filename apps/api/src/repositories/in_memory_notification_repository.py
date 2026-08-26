from __future__ import annotations

from dataclasses import replace

from apps.api.src.models.notification import Notification


class InMemoryNotificationRepository:
    def __init__(self) -> None:
        self._notifications: dict[str, Notification] = {}

    def list_for_worker(self, worker_id: str, limit: int = 50) -> list[Notification]:
        return self.list_for_recipient("worker", worker_id, limit)

    def list_for_recipient(
        self,
        recipient_kind: str,
        recipient_id: str,
        limit: int,
        cursor: tuple[object, str] | None = None,
    ) -> list[Notification]:
        items = [n for n in self._notifications.values() if _recipient_id(n, recipient_kind) == recipient_id]
        items.sort(key=lambda n: (n.created_at, n.notification_id), reverse=True)
        if cursor is not None:
            items = [n for n in items if (n.created_at, n.notification_id) < cursor]
        return items[:limit]

    def unread_count(self, recipient_kind: str, recipient_id: str) -> int:
        return sum(not item.read for item in self.list_for_recipient(recipient_kind, recipient_id, 10000))

    def mark_read(self, notification_id: str, recipient_kind: str, recipient_id: str) -> bool:
        notification = self._notifications.get(notification_id)
        if notification is None or _recipient_id(notification, recipient_kind) != recipient_id:
            return False
        self._notifications[notification_id] = replace(notification, read=True)
        return True

    def save(self, notification: Notification) -> Notification:
        self._notifications[notification.notification_id] = notification
        return notification

    def mark_all_read(self, worker_id: str) -> int:
        return self.mark_all_read_for_recipient("worker", worker_id)

    def mark_all_read_for_recipient(self, recipient_kind: str, recipient_id: str) -> int:
        count = 0
        for notification_id, notification in self._notifications.items():
            if _recipient_id(notification, recipient_kind) == recipient_id and not notification.read:
                self._notifications[notification_id] = replace(notification, read=True)
                count += 1
        return count

    def clear(self) -> None:
        self._notifications.clear()


def _recipient_id(notification: Notification, recipient_kind: str) -> str | None:
    return notification.worker_id if recipient_kind == "worker" else notification.venue_id

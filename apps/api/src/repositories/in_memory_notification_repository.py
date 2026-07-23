from __future__ import annotations

from typing import Dict

from apps.api.src.models.notification import Notification


class InMemoryNotificationRepository:
    def __init__(self) -> None:
        self._notifications: Dict[str, Notification] = {}

    def list_for_worker(self, worker_id: str, limit: int = 50) -> list[Notification]:
        items = [n for n in self._notifications.values() if n.worker_id == worker_id]
        items.sort(key=lambda n: n.created_at, reverse=True)
        return items[:limit]

    def save(self, notification: Notification) -> Notification:
        self._notifications[notification.notification_id] = notification
        return notification

    def mark_all_read(self, worker_id: str) -> int:
        count = 0
        for notification_id, notification in self._notifications.items():
            if notification.worker_id == worker_id and not notification.read:
                self._notifications[notification_id] = _mark_read(notification)
                count += 1
        return count

    def clear(self) -> None:
        self._notifications.clear()


def _mark_read(notification: Notification) -> Notification:
    from dataclasses import replace

    return replace(notification, read=True)

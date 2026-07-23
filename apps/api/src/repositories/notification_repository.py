from __future__ import annotations

from typing import Protocol

from apps.api.src.models.notification import Notification


class NotificationRepository(Protocol):
    def list_for_worker(self, worker_id: str, limit: int = 50) -> list[Notification]: ...
    def save(self, notification: Notification) -> Notification: ...
    def mark_all_read(self, worker_id: str) -> int: ...

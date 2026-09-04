from __future__ import annotations

from typing import Protocol

from apps.api.src.models.notification import Notification


class NotificationRepository(Protocol):
    def list_for_worker(self, worker_id: str, limit: int = 50) -> list[Notification]: ...
    def list_for_recipient(
        self,
        recipient_kind: str,
        recipient_id: str,
        limit: int,
        cursor: tuple[object, str] | None = None,
        viewer_user_id: str | None = None,
    ) -> list[Notification]: ...
    def unread_count(
        self, recipient_kind: str, recipient_id: str, viewer_user_id: str | None = None
    ) -> int: ...
    def mark_read(
        self,
        notification_id: str,
        recipient_kind: str,
        recipient_id: str,
        viewer_user_id: str | None = None,
    ) -> bool: ...
    def save(self, notification: Notification) -> Notification: ...
    def mark_all_read(self, worker_id: str) -> int: ...
    def mark_all_read_for_recipient(
        self, recipient_kind: str, recipient_id: str, viewer_user_id: str | None = None
    ) -> int: ...

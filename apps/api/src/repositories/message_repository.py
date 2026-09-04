from __future__ import annotations

from typing import Protocol

from apps.api.src.models.message import Message


class MessageRepository(Protocol):
    def get(self, message_id: str) -> Message | None:
        ...

    def save(self, message: Message) -> Message:
        ...

    def list_by_shift(self, shift_id: str, limit: int = 100) -> list[Message]:
        ...

    def list_by_thread(self, thread_id: str, limit: int = 100) -> list[Message]:
        ...

    def list_by_application(self, application_id: str, limit: int = 100) -> list[Message]:
        ...

    def list_by_booking(self, booking_id: str, limit: int = 100) -> list[Message]:
        ...

    def list_for_threads_between(
        self, thread_ids: list[str], since, until
    ) -> list[Message]:
        ...

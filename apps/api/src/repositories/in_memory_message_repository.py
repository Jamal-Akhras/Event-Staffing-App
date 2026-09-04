from __future__ import annotations

from collections.abc import Iterable

from apps.api.src.models.message import Message


class InMemoryMessageRepository:
    def __init__(self) -> None:
        self._messages: dict[str, Message] = {}

    def get(self, message_id: str) -> Message | None:
        return self._messages.get(message_id)

    def save(self, message: Message) -> Message:
        existing = self._messages.get(message.message_id)
        if existing is not None:
            if existing != message:
                raise ValueError("Messages are immutable.")
            return existing
        self._messages[message.message_id] = message
        return message

    def list_by_shift(self, shift_id: str, limit: int = 100) -> list[Message]:
        raise RuntimeError("Thread metadata is required to list messages by shift.")

    def list_by_thread(self, thread_id: str, limit: int = 100) -> list[Message]:
        return self._sorted(
            message for message in self._messages.values() if message.thread_id == thread_id
        )[-limit:]

    def list_by_application(self, application_id: str, limit: int = 100) -> list[Message]:
        raise RuntimeError("Thread metadata is required to list messages by application.")

    def list_by_booking(self, booking_id: str, limit: int = 100) -> list[Message]:
        raise RuntimeError("Thread metadata is required to list messages by booking.")

    def list_for_threads_between(self, thread_ids: list[str], since, until) -> list[Message]:
        selected = set(thread_ids)
        return self._sorted(
            message
            for message in self._messages.values()
            if message.thread_id in selected and since <= message.created_at < until
        )

    def clear(self) -> None:
        self._messages.clear()

    @staticmethod
    def _sorted(messages: Iterable[Message]) -> list[Message]:
        items = list(messages)
        items.sort(key=lambda item: item.created_at)
        return items

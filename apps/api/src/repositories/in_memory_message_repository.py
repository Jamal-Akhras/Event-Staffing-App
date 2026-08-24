from __future__ import annotations

from collections.abc import Iterable

from apps.api.src.datetime_utils import utc_now
from apps.api.src.models.message import Message


class InMemoryMessageRepository:
    def __init__(self) -> None:
        self._messages: dict[str, Message] = {}

    def get(self, message_id: str) -> Message | None:
        return self._messages.get(message_id)

    def save(self, message: Message) -> Message:
        self._messages[message.message_id] = message
        return message

    def list_by_shift(self, shift_id: str, limit: int = 100) -> list[Message]:
        return self._sorted(
            message for message in self._messages.values()
            if message.shift_id == shift_id
        )[-limit:]

    def list_by_application(self, application_id: str, limit: int = 100) -> list[Message]:
        return self._sorted(
            message for message in self._messages.values()
            if message.application_id == application_id
        )[-limit:]

    def list_by_booking(self, booking_id: str, limit: int = 100) -> list[Message]:
        return self._sorted(
            message for message in self._messages.values()
            if message.booking_id == booking_id
        )[-limit:]

    def mark_as_read(self, message_id: str) -> bool:
        message = self._messages.get(message_id)
        if message is None:
            return False
        self._messages[message_id] = message.model_copy(
            update={"read_at": utc_now()}
        )
        return True

    def clear(self) -> None:
        self._messages.clear()

    @staticmethod
    def _sorted(messages: Iterable[Message]) -> list[Message]:
        items = list(messages)
        items.sort(key=lambda item: item.created_at)
        return items

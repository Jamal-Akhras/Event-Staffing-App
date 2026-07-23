from __future__ import annotations

from apps.api.src.models.application_message_history import ApplicationMessageHistory


class InMemoryApplicationMessageHistoryRepository:
    def __init__(self) -> None:
        self._items: dict[str, ApplicationMessageHistory] = {}

    def save(self, history: ApplicationMessageHistory) -> ApplicationMessageHistory:
        self._items[history.history_id] = history
        return history

    def list_by_application(self, application_id: str) -> list[ApplicationMessageHistory]:
        items = [
            item for item in self._items.values()
            if item.application_id == application_id
        ]
        items.sort(key=lambda item: item.edited_at)
        return items

    def clear(self) -> None:
        self._items.clear()

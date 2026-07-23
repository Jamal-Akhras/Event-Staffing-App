from __future__ import annotations

from typing import Protocol

from apps.api.src.models.application_message_history import ApplicationMessageHistory


class ApplicationMessageHistoryRepository(Protocol):
    def save(self, history: ApplicationMessageHistory) -> ApplicationMessageHistory:
        raise NotImplementedError

    def list_by_application(self, application_id: str) -> list[ApplicationMessageHistory]:
        raise NotImplementedError

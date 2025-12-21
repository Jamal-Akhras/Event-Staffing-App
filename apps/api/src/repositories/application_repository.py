from __future__ import annotations

from typing import Protocol

from apps.api.src.models.application import Application


class ApplicationRepository(Protocol):
    def get(self, application_id: str) -> Application | None:
        raise NotImplementedError

    def save(self, application: Application) -> Application:
        raise NotImplementedError

    def list_recent(self, limit: int = 50) -> list[Application]:
        raise NotImplementedError

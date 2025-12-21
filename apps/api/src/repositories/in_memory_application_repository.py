from __future__ import annotations

from typing import Dict

from apps.api.src.models.application import Application


class InMemoryApplicationRepository:
    def __init__(self) -> None:
        self._applications: Dict[str, Application] = {}

    def get(self, application_id: str) -> Application | None:
        return self._applications.get(application_id)

    def save(self, application: Application) -> Application:
        self._applications[application.application_id] = application
        return application

    def list_recent(self, limit: int = 50) -> list[Application]:
        items = list(self._applications.values())
        items.sort(key=lambda item: item.created_at, reverse=True)
        return items[:limit]

    def clear(self) -> None:
        self._applications.clear()

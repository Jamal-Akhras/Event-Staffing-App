from __future__ import annotations

from typing import Protocol

from apps.api.src.models.event import Event, EventQuery


class EventRepository(Protocol):
    def append(self, event: Event) -> Event: ...

    def query(self, query: EventQuery) -> list[Event]: ...

    def count_by_name(self, query: EventQuery) -> dict[str, int]: ...

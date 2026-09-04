from __future__ import annotations

from apps.api.src.models.consent import ConsentEvent


class InMemoryConsentRepository:
    def __init__(self) -> None:
        self._events: list[ConsentEvent] = []

    def clear(self) -> None:
        self._events.clear()

    def append(self, event: ConsentEvent) -> ConsentEvent:
        self._events.append(event)
        return event

    def list_for_user(self, user_id: str) -> list[ConsentEvent]:
        rows = [event for event in self._events if event.user_id == user_id]
        return sorted(rows, key=lambda event: event.occurred_at)

    def latest_for_purpose(self, user_id: str, purpose: str) -> ConsentEvent | None:
        rows = [
            event
            for event in self._events
            if event.user_id == user_id and event.purpose == purpose
        ]
        if not rows:
            return None
        return max(rows, key=lambda event: event.occurred_at)

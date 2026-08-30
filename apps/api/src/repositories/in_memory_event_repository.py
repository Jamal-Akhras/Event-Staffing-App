from __future__ import annotations

from collections import Counter

from apps.api.src.models.event import Event, EventQuery


class InMemoryEventRepository:
    def __init__(self) -> None:
        self._events: list[Event] = []

    def append(self, event: Event) -> Event:
        self._events.append(event)
        return event

    def query(self, query: EventQuery) -> list[Event]:
        matches = [event for event in self._events if _matches(event, query)]
        matches.sort(key=lambda event: (event.recorded_at, event.event_id), reverse=True)
        if query.before_id:
            ids = [event.event_id for event in matches]
            if query.before_id in ids:
                matches = matches[ids.index(query.before_id) + 1 :]
        return matches[: query.limit]

    def count_by_name(self, query: EventQuery) -> dict[str, int]:
        counts = Counter(event.name for event in self._events if _matches(event, query))
        return dict(counts.most_common())

    def clear(self) -> None:
        self._events.clear()


def _matches(event: Event, query: EventQuery) -> bool:
    checks = (
        (query.name, event.name),
        (query.category, event.category),
        (query.source, event.source),
        (query.actor_user_id, event.actor_user_id),
        (query.venue_id, event.venue_id),
        (query.worker_id, event.worker_id),
        (query.subject_type, event.subject_type),
        (query.subject_id, event.subject_id),
        (query.slate_id, event.slate_id),
    )
    if any(wanted is not None and wanted != actual for wanted, actual in checks):
        return False
    if query.since is not None and event.occurred_at < query.since:
        return False
    if query.until is not None and event.occurred_at > query.until:
        return False
    return True

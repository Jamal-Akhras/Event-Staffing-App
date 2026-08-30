from __future__ import annotations

from sqlalchemy import and_, desc, func, or_, select
from sqlalchemy.orm import Session

from apps.api.src.db.event_models import EventModel
from apps.api.src.models.event import Event, EventQuery

_FILTERS = (
    ("name", EventModel.name),
    ("category", EventModel.category),
    ("source", EventModel.source),
    ("actor_user_id", EventModel.actor_user_id),
    ("venue_id", EventModel.venue_id),
    ("worker_id", EventModel.worker_id),
    ("subject_type", EventModel.subject_type),
    ("subject_id", EventModel.subject_id),
    ("slate_id", EventModel.slate_id),
)


class SqlAlchemyEventRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def append(self, event: Event) -> Event:
        self._session.add(EventModel(**{name: getattr(event, name) for name in Event.__dataclass_fields__}))
        self._session.flush()
        return event

    def query(self, query: EventQuery) -> list[Event]:
        statement = _apply(select(EventModel), query)
        if query.before_id:
            anchor = self._session.get(EventModel, query.before_id)
            if anchor is not None:
                statement = statement.where(
                    or_(
                        EventModel.recorded_at < anchor.recorded_at,
                        and_(
                            EventModel.recorded_at == anchor.recorded_at,
                            EventModel.event_id < anchor.event_id,
                        ),
                    )
                )
        rows = self._session.execute(
            statement.order_by(desc(EventModel.recorded_at), desc(EventModel.event_id)).limit(query.limit)
        ).scalars().all()
        return [_to_domain(row) for row in rows]

    def count_by_name(self, query: EventQuery) -> dict[str, int]:
        statement = _apply(select(EventModel.name, func.count()).group_by(EventModel.name), query)
        rows = self._session.execute(statement.order_by(desc(func.count()))).all()
        return {name: count for name, count in rows}


def _apply(statement, query: EventQuery):
    for attribute, column in _FILTERS:
        value = getattr(query, attribute)
        if value is not None:
            statement = statement.where(column == value)
    if query.since is not None:
        statement = statement.where(EventModel.occurred_at >= query.since)
    if query.until is not None:
        statement = statement.where(EventModel.occurred_at <= query.until)
    return statement


def _to_domain(row: EventModel) -> Event:
    return Event(**{name: getattr(row, name) for name in Event.__dataclass_fields__})

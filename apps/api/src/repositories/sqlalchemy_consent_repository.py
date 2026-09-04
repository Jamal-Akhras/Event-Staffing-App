from __future__ import annotations

from dataclasses import fields

from sqlalchemy import desc
from sqlalchemy.orm import Session

from apps.api.src.db.consent_models import ConsentEventModel
from apps.api.src.models.consent import ConsentEvent

_FIELDS = tuple(field.name for field in fields(ConsentEvent))


class SqlAlchemyConsentRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def append(self, event: ConsentEvent) -> ConsentEvent:
        self._session.add(ConsentEventModel(**{name: getattr(event, name) for name in _FIELDS}))
        self._session.flush()
        return event

    def list_for_user(self, user_id: str) -> list[ConsentEvent]:
        rows = (
            self._session.query(ConsentEventModel)
            .filter(ConsentEventModel.user_id == user_id)
            .order_by(ConsentEventModel.occurred_at)
            .all()
        )
        return [_to_domain(row) for row in rows]

    def latest_for_purpose(self, user_id: str, purpose: str) -> ConsentEvent | None:
        row = (
            self._session.query(ConsentEventModel)
            .filter(
                ConsentEventModel.user_id == user_id,
                ConsentEventModel.purpose == purpose,
            )
            .order_by(desc(ConsentEventModel.occurred_at))
            .first()
        )
        return _to_domain(row) if row is not None else None


def _to_domain(model: ConsentEventModel) -> ConsentEvent:
    return ConsentEvent(**{name: getattr(model, name) for name in _FIELDS})

from __future__ import annotations

from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from apps.api.src.db.rota_models import RotaPublicationModel
from apps.api.src.models.rota_publication import RotaPublication

_FIELDS = tuple(RotaPublication.__dataclass_fields__)


def _to_domain(row: RotaPublicationModel) -> RotaPublication:
    return RotaPublication(**{name: getattr(row, name) for name in _FIELDS})


class SqlAlchemyRotaPublicationRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def save(self, publication: RotaPublication) -> RotaPublication:
        self._session.add(
            RotaPublicationModel(**{name: getattr(publication, name) for name in _FIELDS})
        )
        self._session.flush()
        return publication

    def latest_for_week(self, venue_id: str, week_start: date) -> RotaPublication | None:
        row = self._session.execute(
            select(RotaPublicationModel)
            .where(
                RotaPublicationModel.venue_id == venue_id,
                RotaPublicationModel.week_start == week_start,
            )
            .order_by(RotaPublicationModel.revision.desc())
            .limit(1)
        ).scalar_one_or_none()
        return _to_domain(row) if row else None

    def list_for_week(self, venue_id: str, week_start: date) -> list[RotaPublication]:
        rows = self._session.execute(
            select(RotaPublicationModel)
            .where(
                RotaPublicationModel.venue_id == venue_id,
                RotaPublicationModel.week_start == week_start,
            )
            .order_by(RotaPublicationModel.revision)
        ).scalars().all()
        return [_to_domain(row) for row in rows]

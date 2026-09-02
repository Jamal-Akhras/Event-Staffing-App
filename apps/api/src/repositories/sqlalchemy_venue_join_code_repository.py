from __future__ import annotations

from contextlib import contextmanager

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from apps.api.src.db.workforce_models import VenueJoinCodeModel, VenueJoinCodeRedemptionModel
from apps.api.src.models.venue_join_code import VenueJoinCode, VenueJoinCodeRedemption
from apps.api.src.repositories.venue_join_code_repository import JoinCodeExhaustedError

_CODE_FIELDS = tuple(VenueJoinCode.__dataclass_fields__)
_REDEMPTION_FIELDS = tuple(VenueJoinCodeRedemption.__dataclass_fields__)


def _to_code(row: VenueJoinCodeModel) -> VenueJoinCode:
    return VenueJoinCode(**{name: getattr(row, name) for name in _CODE_FIELDS})


def _to_redemption(row: VenueJoinCodeRedemptionModel) -> VenueJoinCodeRedemption:
    return VenueJoinCodeRedemption(**{name: getattr(row, name) for name in _REDEMPTION_FIELDS})


class SqlAlchemyVenueJoinCodeRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def save_code(self, code: VenueJoinCode) -> VenueJoinCode:
        values = {name: getattr(code, name) for name in _CODE_FIELDS}
        row = self._session.get(VenueJoinCodeModel, code.code)
        if row is None:
            self._session.add(VenueJoinCodeModel(**values))
        else:
            for name, value in values.items():
                setattr(row, name, value)
        self._session.flush()
        return code

    def get_code(self, code: str) -> VenueJoinCode | None:
        row = self._session.get(VenueJoinCodeModel, code)
        return _to_code(row) if row else None

    def list_codes_for_venue(self, venue_id: str) -> list[VenueJoinCode]:
        rows = self._session.execute(
            select(VenueJoinCodeModel)
            .where(VenueJoinCodeModel.venue_id == venue_id)
            .order_by(VenueJoinCodeModel.created_at)
        ).scalars().all()
        return [_to_code(row) for row in rows]

    def count_redemptions(self, code: str) -> int:
        return self._session.execute(
            select(func.count())
            .select_from(VenueJoinCodeRedemptionModel)
            .where(VenueJoinCodeRedemptionModel.code == code)
        ).scalar_one()

    def list_redemptions(self, code: str) -> list[VenueJoinCodeRedemption]:
        rows = self._session.execute(
            select(VenueJoinCodeRedemptionModel)
            .where(VenueJoinCodeRedemptionModel.code == code)
            .order_by(VenueJoinCodeRedemptionModel.redeemed_at)
        ).scalars().all()
        return [_to_redemption(row) for row in rows]

    @contextmanager
    def redemption_guard(self, code: str, max_redemptions: int):
        self._session.execute(
            select(VenueJoinCodeModel).where(VenueJoinCodeModel.code == code).with_for_update()
        ).scalar_one()
        if self.count_redemptions(code) >= max_redemptions:
            raise JoinCodeExhaustedError(code)
        yield

    def save_redemption(self, redemption: VenueJoinCodeRedemption) -> VenueJoinCodeRedemption:
        self._session.add(
            VenueJoinCodeRedemptionModel(**{name: getattr(redemption, name) for name in _REDEMPTION_FIELDS})
        )
        self._session.flush()
        return redemption

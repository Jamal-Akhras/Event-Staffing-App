from __future__ import annotations

from sqlalchemy.orm import Session

from apps.api.src.db.billing_models import PartnerCodeModel, PartnerCodeRedemptionModel
from apps.api.src.db.tenancy_models import VenueModel
from apps.api.src.models.partner_code import PartnerCode, PartnerCodeRedemption


class SqlAlchemyPartnerCodeRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def get_code(self, code: str) -> PartnerCode | None:
        row = self._session.get(PartnerCodeModel, code)
        return _code_to_domain(row) if row is not None else None

    def get_code_for_redemption(self, code: str, account_id: str) -> PartnerCode | None:
        venue = (
            self._session.query(VenueModel)
            .filter(VenueModel.venue_id == account_id)
            .with_for_update()
            .one_or_none()
        )
        if venue is None:
            return None
        row = (
            self._session.query(PartnerCodeModel)
            .filter(PartnerCodeModel.code == code)
            .with_for_update()
            .one_or_none()
        )
        return _code_to_domain(row) if row is not None else None

    def save_code(self, partner_code: PartnerCode) -> PartnerCode:
        row = self._session.get(PartnerCodeModel, partner_code.code)
        if row is None:
            row = PartnerCodeModel(code=partner_code.code)
            self._session.add(row)
        for name in PartnerCode.__dataclass_fields__:
            if name != "code":
                setattr(row, name, getattr(partner_code, name))
        self._session.flush()
        return partner_code

    def list_redemptions(self, code: str) -> list[PartnerCodeRedemption]:
        rows = (
            self._session.query(PartnerCodeRedemptionModel)
            .filter(PartnerCodeRedemptionModel.code == code)
            .order_by(PartnerCodeRedemptionModel.redeemed_at)
            .all()
        )
        return [_redemption_to_domain(row) for row in rows]

    def get_redemption_for_account(self, account_id: str) -> PartnerCodeRedemption | None:
        row = (
            self._session.query(PartnerCodeRedemptionModel)
            .filter(PartnerCodeRedemptionModel.account_id == account_id)
            .one_or_none()
        )
        return _redemption_to_domain(row) if row is not None else None

    def save_redemption(self, redemption: PartnerCodeRedemption) -> PartnerCodeRedemption:
        row = PartnerCodeRedemptionModel(**redemption.__dict__)
        self._session.add(row)
        self._session.flush()
        return redemption


def _code_to_domain(row: PartnerCodeModel) -> PartnerCode:
    return PartnerCode(**{name: getattr(row, name) for name in PartnerCode.__dataclass_fields__})


def _redemption_to_domain(row: PartnerCodeRedemptionModel) -> PartnerCodeRedemption:
    return PartnerCodeRedemption(**{name: getattr(row, name) for name in PartnerCodeRedemption.__dataclass_fields__})

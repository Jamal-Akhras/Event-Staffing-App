from __future__ import annotations

from dataclasses import fields

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from apps.api.src.db.commercial_models import (
    CommercialAgreementModel,
    ShiftBoostModel,
    SubscriptionChargeModel,
)
from apps.api.src.models.commercial import (
    CommercialAgreement,
    ShiftBoost,
    SubscriptionCharge,
)
from apps.api.src.repositories.commercial_repository import (
    DuplicateActiveBoostError,
    DuplicateSubscriptionChargeError,
)

_AGREEMENT_FIELDS = tuple(field.name for field in fields(CommercialAgreement))
_SUBSCRIPTION_FIELDS = tuple(field.name for field in fields(SubscriptionCharge))
_BOOST_FIELDS = tuple(field.name for field in fields(ShiftBoost))


class SqlAlchemyCommercialAgreementRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def save(self, agreement: CommercialAgreement) -> CommercialAgreement:
        model = self._session.get(CommercialAgreementModel, agreement.agreement_id)
        if model is None:
            model = CommercialAgreementModel(agreement_id=agreement.agreement_id)
            self._session.add(model)
        for name in _AGREEMENT_FIELDS:
            setattr(model, name, getattr(agreement, name))
        self._session.flush()
        return agreement

    def list_for_organisation(self, organisation_id: str) -> list[CommercialAgreement]:
        rows = (
            self._session.query(CommercialAgreementModel)
            .filter(CommercialAgreementModel.organisation_id == organisation_id)
            .order_by(CommercialAgreementModel.effective_from)
            .all()
        )
        return [_agreement(row) for row in rows]


class SqlAlchemySubscriptionChargeRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def save(self, charge: SubscriptionCharge) -> SubscriptionCharge:
        try:
            with self._session.begin_nested():
                model = SubscriptionChargeModel(
                    **{name: getattr(charge, name) for name in _SUBSCRIPTION_FIELDS}
                )
                self._session.add(model)
                self._session.flush()
        except IntegrityError as exc:
            raise DuplicateSubscriptionChargeError(charge.venue_id) from exc
        return charge

    def get_for_venue_period(self, venue_id: str, period: str) -> SubscriptionCharge | None:
        row = (
            self._session.query(SubscriptionChargeModel)
            .filter(
                SubscriptionChargeModel.venue_id == venue_id,
                SubscriptionChargeModel.period == period,
            )
            .one_or_none()
        )
        return _subscription(row) if row is not None else None

    def list_for_organisation_period(
        self, organisation_id: str, period: str
    ) -> list[SubscriptionCharge]:
        rows = (
            self._session.query(SubscriptionChargeModel)
            .filter(
                SubscriptionChargeModel.organisation_id == organisation_id,
                SubscriptionChargeModel.period == period,
            )
            .order_by(SubscriptionChargeModel.venue_id)
            .all()
        )
        return [_subscription(row) for row in rows]


class SqlAlchemyShiftBoostRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def save(self, boost: ShiftBoost) -> ShiftBoost:
        try:
            with self._session.begin_nested():
                model = self._session.get(ShiftBoostModel, boost.boost_id)
                if model is None:
                    model = ShiftBoostModel(boost_id=boost.boost_id)
                    self._session.add(model)
                for name in _BOOST_FIELDS:
                    setattr(model, name, getattr(boost, name))
                self._session.flush()
        except IntegrityError as exc:
            raise DuplicateActiveBoostError(boost.shift_id) from exc
        return boost

    def get_active_for_shift(self, shift_id: str) -> ShiftBoost | None:
        row = (
            self._session.query(ShiftBoostModel)
            .filter(ShiftBoostModel.shift_id == shift_id, ShiftBoostModel.status == "active")
            .one_or_none()
        )
        return _boost(row) if row is not None else None

    def list_for_venue_period(self, venue_id: str, period: str) -> list[ShiftBoost]:
        rows = (
            self._session.query(ShiftBoostModel)
            .filter(ShiftBoostModel.venue_id == venue_id, ShiftBoostModel.period == period)
            .order_by(ShiftBoostModel.purchased_at)
            .all()
        )
        return [_boost(row) for row in rows]


def _agreement(model: CommercialAgreementModel) -> CommercialAgreement:
    return CommercialAgreement(**{name: getattr(model, name) for name in _AGREEMENT_FIELDS})


def _subscription(model: SubscriptionChargeModel) -> SubscriptionCharge:
    return SubscriptionCharge(**{name: getattr(model, name) for name in _SUBSCRIPTION_FIELDS})


def _boost(model: ShiftBoostModel) -> ShiftBoost:
    return ShiftBoost(**{name: getattr(model, name) for name in _BOOST_FIELDS})

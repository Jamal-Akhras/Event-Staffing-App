from __future__ import annotations

from dataclasses import fields
from datetime import datetime

from sqlalchemy import desc, or_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from apps.api.src.db.shift_offer_models import ShiftOfferModel
from apps.api.src.models.shift_offer import ShiftOffer
from apps.api.src.repositories.shift_offer_repository import DuplicatePendingOfferError

_FIELDS = tuple(field.name for field in fields(ShiftOffer))


class SqlAlchemyShiftOfferRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def save(self, offer: ShiftOffer) -> ShiftOffer:
        try:
            with self._session.begin_nested():
                model = self._session.get(ShiftOfferModel, offer.offer_id)
                if model is None:
                    model = ShiftOfferModel(offer_id=offer.offer_id)
                    self._session.add(model)
                for name in _FIELDS:
                    setattr(model, name, getattr(offer, name))
                self._session.flush()
        except IntegrityError as exc:
            raise DuplicatePendingOfferError(
                f"Shift {offer.shift_id} already has a pending offer."
            ) from exc
        return offer

    def get(self, offer_id: str) -> ShiftOffer | None:
        model = self._session.get(ShiftOfferModel, offer_id)
        return _to_domain(model) if model is not None else None

    def get_pending_for_shift(self, shift_id: str) -> ShiftOffer | None:
        model = (
            self._session.query(ShiftOfferModel)
            .filter(ShiftOfferModel.shift_id == shift_id)
            .filter(ShiftOfferModel.status == "pending")
            .one_or_none()
        )
        return _to_domain(model) if model is not None else None

    def list_for_worker(self, worker_id: str) -> list[ShiftOffer]:
        rows = (
            self._session.query(ShiftOfferModel)
            .filter(ShiftOfferModel.worker_id == worker_id)
            .order_by(desc(ShiftOfferModel.offered_at))
            .all()
        )
        return [_to_domain(row) for row in rows]

    def list_pending_for_worker(self, worker_id: str) -> list[ShiftOffer]:
        rows = (
            self._session.query(ShiftOfferModel)
            .filter(ShiftOfferModel.worker_id == worker_id)
            .filter(ShiftOfferModel.status == "pending")
            .order_by(desc(ShiftOfferModel.offered_at))
            .all()
        )
        return [_to_domain(row) for row in rows]

    def claim_pending_unexpired(self, now: datetime) -> list[ShiftOffer]:
        query = (
            self._session.query(ShiftOfferModel)
            .filter(ShiftOfferModel.status == "pending")
            .filter(
                or_(ShiftOfferModel.expires_at.is_(None), ShiftOfferModel.expires_at > now)
            )
            .order_by(ShiftOfferModel.offered_at)
        )
        if self._session.bind is not None and self._session.bind.dialect.name == "postgresql":
            query = query.with_for_update(skip_locked=True)
        return [_to_domain(row) for row in query.all()]


def _to_domain(model: ShiftOfferModel) -> ShiftOffer:
    return ShiftOffer(**{name: getattr(model, name) for name in _FIELDS})

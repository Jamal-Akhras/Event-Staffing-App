from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from apps.api.src.db.booking_charge_models import BookingChargeAdjustmentModel
from apps.api.src.models.booking_charge_adjustment import BookingChargeAdjustment

_FIELDS = tuple(BookingChargeAdjustment.__dataclass_fields__)


def _to_domain(row: BookingChargeAdjustmentModel) -> BookingChargeAdjustment:
    return BookingChargeAdjustment(**{name: getattr(row, name) for name in _FIELDS})


class SqlAlchemyBookingChargeAdjustmentRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def record(self, adjustment: BookingChargeAdjustment) -> BookingChargeAdjustment:
        self._session.add(
            BookingChargeAdjustmentModel(**{name: getattr(adjustment, name) for name in _FIELDS})
        )
        self._session.flush()
        return adjustment

    def list_for_charge(self, charge_id: str) -> list[BookingChargeAdjustment]:
        rows = self._session.execute(
            select(BookingChargeAdjustmentModel)
            .where(BookingChargeAdjustmentModel.charge_id == charge_id)
            .order_by(BookingChargeAdjustmentModel.created_at)
        ).scalars().all()
        return [_to_domain(row) for row in rows]

    def list_for_charges(self, charge_ids: list[str]) -> list[BookingChargeAdjustment]:
        if not charge_ids:
            return []
        rows = self._session.execute(
            select(BookingChargeAdjustmentModel)
            .where(BookingChargeAdjustmentModel.charge_id.in_(charge_ids))
            .order_by(BookingChargeAdjustmentModel.created_at)
        ).scalars().all()
        return [_to_domain(row) for row in rows]

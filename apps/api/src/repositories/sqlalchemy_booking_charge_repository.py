from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from apps.api.src.db.booking_charge_models import BookingChargeModel
from apps.api.src.models.booking_charge import BookingCharge

_FIELDS = tuple(BookingCharge.__dataclass_fields__)


def _to_domain(row: BookingChargeModel) -> BookingCharge:
    return BookingCharge(**{name: getattr(row, name) for name in _FIELDS})


class SqlAlchemyBookingChargeRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def record(self, charge: BookingCharge) -> BookingCharge:
        self._session.add(BookingChargeModel(**{name: getattr(charge, name) for name in _FIELDS}))
        self._session.flush()
        return charge

    def get_for_booking(self, booking_id: str) -> BookingCharge | None:
        row = self._session.execute(
            select(BookingChargeModel).where(BookingChargeModel.booking_id == booking_id)
        ).scalar_one_or_none()
        return _to_domain(row) if row else None

    def list_for_worker(self, worker_id: str) -> list[BookingCharge]:
        rows = self._session.execute(
            select(BookingChargeModel)
            .where(BookingChargeModel.worker_id == worker_id)
            .order_by(BookingChargeModel.completed_at)
        ).scalars().all()
        return [_to_domain(row) for row in rows]

    def list_for_account(self, account_id: str, period: str | None = None) -> list[BookingCharge]:
        query = select(BookingChargeModel).where(BookingChargeModel.account_id == account_id)
        if period is not None:
            query = query.where(BookingChargeModel.period == period)
        rows = self._session.execute(query.order_by(BookingChargeModel.completed_at)).scalars().all()
        return [_to_domain(row) for row in rows]

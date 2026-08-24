from __future__ import annotations

from sqlalchemy import desc
from sqlalchemy.orm import Session

from apps.api.src.db.models import BookingModel, ShiftModel
from apps.api.src.money import money
from apps.api.src.models.shift import Shift


class SqlAlchemyShiftRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def get(self, shift_id: str) -> Shift | None:
        model = self._session.get(ShiftModel, shift_id)
        if model is None:
            return None
        return _to_domain(model)

    def get_for_update(self, shift_id: str) -> Shift | None:
        model = (
            self._session.query(ShiftModel)
            .filter(ShiftModel.shift_id == shift_id)
            .with_for_update()
            .one_or_none()
        )
        return _to_domain(model) if model is not None else None

    def save(self, shift: Shift) -> Shift:
        model = self._session.get(ShiftModel, shift.shift_id)
        if model is None:
            model = ShiftModel(shift_id=shift.shift_id)
            self._session.add(model)
        _apply_domain(model, shift)
        self._session.flush()
        return shift

    def list_recent(self, limit: int = 50) -> list[Shift]:
        rows = (
            self._session.query(ShiftModel)
            .order_by(desc(ShiftModel.created_at))
            .limit(limit)
            .all()
        )
        return [_to_domain(row) for row in rows]

    def list_for_account(self, account_id: str, limit: int = 50) -> list[Shift]:
        rows = (
            self._session.query(ShiftModel)
            .filter(ShiftModel.account_id == account_id)
            .order_by(desc(ShiftModel.created_at))
            .limit(limit)
            .all()
        )
        return [_to_domain(row) for row in rows]

    def list_by_worker(self, worker_id: str, limit: int = 50) -> list[Shift]:
        rows = (
            self._session.query(ShiftModel)
            .join(BookingModel, BookingModel.shift_id == ShiftModel.shift_id)
            .filter(BookingModel.worker_id == worker_id)
            .order_by(desc(ShiftModel.created_at))
            .limit(limit)
            .all()
        )
        return [_to_domain(row) for row in rows]


def _to_domain(model: ShiftModel) -> Shift:
    return Shift(
        shift_id=model.shift_id,
        operator_id=model.operator_id,
        role=model.role,
        location=model.location,
        start_time=model.start_time,
        end_time=model.end_time,
        pay_rate=money(model.pay_rate),
        notes=model.notes,
        status=model.status,
        created_at=model.created_at,
        workers_needed=model.workers_needed,
        workers_filled=model.workers_filled,
        account_id=getattr(model, "account_id", None),
        currency=getattr(model, "currency", None) or "GBP",
        latitude=getattr(model, "latitude", None),
        longitude=getattr(model, "longitude", None),
        updated_at=getattr(model, "updated_at", None),
        closed_at=getattr(model, "closed_at", None),
        cancelled_at=getattr(model, "cancelled_at", None),
        cancellation_reason=getattr(model, "cancellation_reason", None),
        cancelled_by_user_id=getattr(model, "cancelled_by_user_id", None),
    )


def _apply_domain(model: ShiftModel, shift: Shift) -> None:
    model.operator_id = shift.operator_id
    model.role = shift.role
    model.location = shift.location
    model.start_time = shift.start_time
    model.end_time = shift.end_time
    model.pay_rate = money(shift.pay_rate)
    model.notes = shift.notes
    model.status = shift.status
    model.created_at = shift.created_at
    model.workers_needed = shift.workers_needed
    model.workers_filled = shift.workers_filled
    model.account_id = shift.account_id
    model.currency = shift.currency
    model.latitude = shift.latitude
    model.longitude = shift.longitude
    model.updated_at = shift.updated_at or shift.created_at
    model.closed_at = shift.closed_at
    model.cancelled_at = shift.cancelled_at
    model.cancellation_reason = shift.cancellation_reason
    model.cancelled_by_user_id = shift.cancelled_by_user_id

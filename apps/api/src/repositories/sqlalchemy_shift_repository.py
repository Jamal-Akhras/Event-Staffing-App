from __future__ import annotations

from sqlalchemy import desc
from sqlalchemy.orm import Session

from apps.api.src.db.models import ShiftModel
from apps.api.src.models.shift import Shift


class SqlAlchemyShiftRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def get(self, shift_id: str) -> Shift | None:
        model = self._session.get(ShiftModel, shift_id)
        if model is None:
            return None
        return _to_domain(model)

    def save(self, shift: Shift) -> Shift:
        model = self._session.get(ShiftModel, shift.shift_id)
        if model is None:
            model = ShiftModel(shift_id=shift.shift_id)
            self._session.add(model)
        _apply_domain(model, shift)
        self._session.commit()
        return shift

    def list_recent(self, limit: int = 50) -> list[Shift]:
        rows = (
            self._session.query(ShiftModel)
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
        pay_rate=model.pay_rate,
        notes=model.notes,
        status=model.status,
        created_at=model.created_at,
    )


def _apply_domain(model: ShiftModel, shift: Shift) -> None:
    model.operator_id = shift.operator_id
    model.role = shift.role
    model.location = shift.location
    model.start_time = shift.start_time
    model.end_time = shift.end_time
    model.pay_rate = shift.pay_rate
    model.notes = shift.notes
    model.status = shift.status
    model.created_at = shift.created_at

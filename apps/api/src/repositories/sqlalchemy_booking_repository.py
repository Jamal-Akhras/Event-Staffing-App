from __future__ import annotations

from sqlalchemy import desc
from sqlalchemy.orm import Session

from apps.api.src.db.models import BookingModel
from packages.domain.src.booking import Booking
from packages.domain.src.booking_state import BookingState


class SqlAlchemyBookingRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def get(self, booking_id: str) -> Booking | None:
        model = self._session.get(BookingModel, booking_id)
        if model is None:
            return None
        return _to_domain(model)

    def save(self, booking: Booking) -> Booking:
        model = self._session.get(BookingModel, booking.booking_id)
        if model is None:
            model = BookingModel(booking_id=booking.booking_id)
            self._session.add(model)
        _apply_domain(model, booking)
        self._session.commit()
        return booking

    def list_recent(self, limit: int = 25) -> list[Booking]:
        rows = (
            self._session.query(BookingModel)
            .order_by(desc(BookingModel.created_at))
            .limit(limit)
            .all()
        )
        return [_to_domain(row) for row in rows]

    def list_by_worker(self, worker_id: str) -> list[Booking]:
        rows = (
            self._session.query(BookingModel)
            .filter(BookingModel.worker_id == worker_id)
            .order_by(desc(BookingModel.created_at))
            .all()
        )
        return [_to_domain(row) for row in rows]

    def list_by_state(self, state: BookingState) -> list[Booking]:
        rows = (
            self._session.query(BookingModel)
            .filter(BookingModel.state == state)
            .order_by(desc(BookingModel.created_at))
            .all()
        )
        return [_to_domain(row) for row in rows]


def _to_domain(model: BookingModel) -> Booking:
    return Booking(
        booking_id=model.booking_id,
        shift_id=model.shift_id,
        worker_id=model.worker_id,
        operator_id=model.operator_id,
        start_time=model.start_time,
        end_time=model.end_time,
        state=model.state,
        created_at=model.created_at,
        confirmed_at=model.confirmed_at,
        checked_in_at=model.checked_in_at,
        checked_out_at=model.checked_out_at,
        approved_at=model.approved_at,
        paid_at=model.paid_at,
        cancelled_at=model.cancelled_at,
        no_show_at=model.no_show_at,
    )


def _apply_domain(model: BookingModel, booking: Booking) -> None:
    model.shift_id = booking.shift_id
    model.worker_id = booking.worker_id
    model.operator_id = booking.operator_id
    model.start_time = booking.start_time
    model.end_time = booking.end_time
    model.state = booking.state
    model.created_at = booking.created_at
    model.confirmed_at = booking.confirmed_at
    model.checked_in_at = booking.checked_in_at
    model.checked_out_at = booking.checked_out_at
    model.approved_at = booking.approved_at
    model.paid_at = booking.paid_at
    model.cancelled_at = booking.cancelled_at
    model.no_show_at = booking.no_show_at

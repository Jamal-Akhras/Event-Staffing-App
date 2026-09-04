from __future__ import annotations

from datetime import datetime

from sqlalchemy import case, desc, func, select
from sqlalchemy.orm import Session

from apps.api.src.db.models import BookingModel, ShiftModel
from apps.api.src.models.insights import AttendanceSummary, WorkerActivity
from apps.api.src.repositories.booking_repository import LIVE_BOOKING_STATES
from packages.domain.src.booking import Booking
from packages.domain.src.booking_state import BookingState

COMPLETED_STATES = (BookingState.CHECKED_OUT, BookingState.APPROVED, BookingState.PAID)
BROKEN_STATES = (BookingState.NO_SHOW, BookingState.CANCELLED_BY_WORKER)


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
        self._session.flush()
        return booking

    def list_recent(self, limit: int = 25) -> list[Booking]:
        rows = (
            self._session.query(BookingModel)
            .order_by(desc(BookingModel.created_at))
            .limit(limit)
            .all()
        )
        return [_to_domain(row) for row in rows]

    def list_by_worker(
        self,
        worker_id: str,
        limit: int | None = None,
        operator_id: str | None = None,
    ) -> list[Booking]:
        return self._list(limit, worker_id=worker_id, operator_id=operator_id)

    def list_by_operator(
        self,
        operator_id: str,
        limit: int = 25,
        worker_id: str | None = None,
    ) -> list[Booking]:
        return self._list(limit, worker_id=worker_id, operator_id=operator_id)

    def list_for_account(
        self,
        account_id: str,
        limit: int = 25,
        worker_id: str | None = None,
    ) -> list[Booking]:
        return self._list(limit, worker_id=worker_id, account_id=account_id)

    def list_by_state(self, state: BookingState) -> list[Booking]:
        rows = (
            self._session.query(BookingModel)
            .filter(BookingModel.state == state)
            .order_by(desc(BookingModel.created_at))
            .all()
        )
        return [_to_domain(row) for row in rows]

    def list_by_shift(self, shift_id: str, for_update: bool = False) -> list[Booking]:
        query = self._session.query(BookingModel).filter(BookingModel.shift_id == shift_id)
        if for_update:
            query = query.with_for_update()
        return [_to_domain(row) for row in query.all()]

    def list_for_shifts(self, shift_ids: list[str]) -> list[Booking]:
        if not shift_ids:
            return []
        rows = (
            self._session.query(BookingModel)
            .filter(BookingModel.shift_id.in_(shift_ids))
            .order_by(BookingModel.start_time)
            .all()
        )
        return [_to_domain(row) for row in rows]

    def list_live_for_workers(self, worker_ids: list[str], at: datetime) -> list[Booking]:
        if not worker_ids:
            return []
        rows = (
            self._session.query(BookingModel)
            .filter(BookingModel.worker_id.in_(worker_ids))
            .filter(BookingModel.state.in_(LIVE_BOOKING_STATES))
            .filter(BookingModel.start_time <= at)
            .filter(BookingModel.end_time > at)
            .order_by(BookingModel.start_time, BookingModel.booking_id)
            .all()
        )
        return [_to_domain(row) for row in rows]

    def list_live_overlapping_for_worker(
        self,
        worker_id: str,
        start_time: datetime,
        end_time: datetime,
        venue_id: str | None = None,
    ) -> list[Booking]:
        query = self._session.query(BookingModel)
        if venue_id is not None:
            query = query.join(ShiftModel, ShiftModel.shift_id == BookingModel.shift_id)
            query = query.filter(ShiftModel.account_id == venue_id)
        rows = (
            query.filter(BookingModel.worker_id == worker_id)
            .filter(BookingModel.state.in_(LIVE_BOOKING_STATES))
            .filter(BookingModel.start_time < end_time)
            .filter(BookingModel.end_time > start_time)
            .order_by(BookingModel.start_time, BookingModel.booking_id)
            .all()
        )
        return [_to_domain(row) for row in rows]

    def attendance_summary(self, account_id: str, since: datetime, until: datetime) -> AttendanceSummary:
        completed = func.count(case((BookingModel.state.in_(COMPLETED_STATES), 1)))
        no_shows = func.count(case((BookingModel.state == BookingState.NO_SHOW, 1)))
        row = self._session.execute(
            select(completed, no_shows)
            .select_from(BookingModel)
            .join(ShiftModel, ShiftModel.shift_id == BookingModel.shift_id)
            .where(ShiftModel.account_id == account_id)
            .where(BookingModel.start_time >= since)
            .where(BookingModel.start_time <= until)
        ).one()
        return AttendanceSummary(completed=row[0], no_shows=row[1])

    def worker_activity(self, account_id: str, broken_since: datetime) -> list[WorkerActivity]:
        completed = func.count(case((BookingModel.state.in_(COMPLETED_STATES), 1)))
        last_worked = func.max(case((BookingModel.state.in_(COMPLETED_STATES), BookingModel.start_time)))
        broken = func.count(
            case(
                (
                    BookingModel.state.in_(BROKEN_STATES) & (BookingModel.start_time >= broken_since),
                    1,
                )
            )
        )
        rows = self._session.execute(
            select(BookingModel.worker_id, completed, last_worked, broken)
            .select_from(BookingModel)
            .join(ShiftModel, ShiftModel.shift_id == BookingModel.shift_id)
            .where(ShiftModel.account_id == account_id)
            .group_by(BookingModel.worker_id)
            .order_by(BookingModel.worker_id)
        ).all()
        return [
            WorkerActivity(
                worker_id=row[0],
                completed=row[1],
                last_worked=row[2],
                recently_broken=row[3] > 0,
            )
            for row in rows
        ]

    def _list(
        self,
        limit: int | None,
        worker_id: str | None = None,
        operator_id: str | None = None,
        account_id: str | None = None,
    ) -> list[Booking]:
        query = self._session.query(BookingModel)
        if account_id:
            query = query.join(ShiftModel, ShiftModel.shift_id == BookingModel.shift_id)
            query = query.filter(ShiftModel.account_id == account_id)
        if worker_id:
            query = query.filter(BookingModel.worker_id == worker_id)
        if operator_id:
            query = query.filter(BookingModel.operator_id == operator_id)
        query = query.order_by(desc(BookingModel.created_at))
        if limit is not None:
            query = query.limit(limit)
        rows = query.all()
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
        cancellation_reason=getattr(model, "cancellation_reason", None),
        cancelled_by_user_id=getattr(model, "cancelled_by_user_id", None),
        no_show_at=model.no_show_at,
        payment_method=getattr(model, "payment_method", None),
        payment_reference=getattr(model, "payment_reference", None),
        payment_recorded_by_user_id=getattr(model, "payment_recorded_by_user_id", None),
        check_in_code=model.check_in_code,
        completion_code=model.completion_code,
        attendance_mode=model.attendance_mode,
        allocation_source=model.allocation_source,
        override_checked_in_at=model.override_checked_in_at,
        override_checked_out_at=model.override_checked_out_at,
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
    model.cancellation_reason = booking.cancellation_reason
    model.cancelled_by_user_id = booking.cancelled_by_user_id
    model.no_show_at = booking.no_show_at
    model.payment_method = booking.payment_method
    model.payment_reference = booking.payment_reference
    model.payment_recorded_by_user_id = booking.payment_recorded_by_user_id
    model.check_in_code = booking.check_in_code
    model.completion_code = booking.completion_code
    model.attendance_mode = booking.attendance_mode
    model.allocation_source = booking.allocation_source
    model.override_checked_in_at = booking.override_checked_in_at
    model.override_checked_out_at = booking.override_checked_out_at

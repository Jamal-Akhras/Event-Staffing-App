from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from apps.api.src.models.shift import Shift
from apps.api.src.repositories.in_memory_booking_repository import InMemoryBookingRepository
from apps.api.src.repositories.in_memory_shift_repository import InMemoryShiftRepository
from apps.api.src.repositories.sqlalchemy_booking_repository import SqlAlchemyBookingRepository
from apps.api.src.repositories.sqlalchemy_shift_repository import SqlAlchemyShiftRepository
from packages.domain.src.booking import Booking
from packages.domain.src.booking_state import BookingState

AT = datetime(2030, 6, 10, 18, tzinfo=UTC)


@pytest.fixture(params=["memory", "database"])
def repositories(request, repo_session):
    if request.param == "memory":
        bookings = InMemoryBookingRepository()
        shifts = InMemoryShiftRepository(bookings)
        bookings.attach_shift_repo(shifts)
        return bookings, shifts, None
    return (
        SqlAlchemyBookingRepository(repo_session),
        SqlAlchemyShiftRepository(repo_session),
        repo_session,
    )


def _shift(shift_id: str, start_time: datetime, end_time: datetime) -> Shift:
    return Shift(
        shift_id=shift_id,
        operator_id="operator-1",
        role="Bartender",
        location="Main bar",
        start_time=start_time,
        end_time=end_time,
        pay_rate=Decimal("15.50"),
        notes=None,
        status="filled",
        created_at=AT - timedelta(days=2),
        workers_needed=1,
        workers_filled=1,
    )


def _booking(booking_id: str, worker_id: str, state: BookingState, offset: int = 0) -> Booking:
    start_time = AT - timedelta(hours=1) + timedelta(minutes=offset)
    return Booking(
        booking_id=booking_id,
        shift_id=f"shift-{booking_id}",
        worker_id=worker_id,
        operator_id="operator-1",
        start_time=start_time,
        end_time=AT + timedelta(hours=2),
        state=state,
        created_at=AT - timedelta(days=1),
        confirmed_at=AT - timedelta(hours=3),
        checked_in_at=AT - timedelta(hours=1),
        checked_out_at=AT - timedelta(minutes=30),
        approved_at=AT - timedelta(minutes=15),
        paid_at=AT - timedelta(minutes=5),
        cancelled_at=AT - timedelta(minutes=4),
        cancellation_reason="Preserved mapper field",
        cancelled_by_user_id="manager-1",
        no_show_at=AT - timedelta(minutes=3),
        payment_method="bank_transfer",
        payment_reference="payment-1",
        payment_recorded_by_user_id="manager-1",
        check_in_code="1234",
        completion_code="5678",
        attendance_mode="employed",
        override_checked_in_at=AT - timedelta(hours=1),
        override_checked_out_at=AT - timedelta(minutes=30),
    )


def test_list_live_for_workers_filters_state_worker_and_interval(repositories):
    bookings, shifts, session = repositories
    selected = _booking("selected", "worker-1", BookingState.APPROVED, 10)
    earlier = _booking("earlier", "worker-2", BookingState.CONFIRMED)
    excluded = [
        _booking("cancelled", "worker-1", BookingState.CANCELLED_BY_WORKER),
        _booking("stranger", "worker-3", BookingState.CONFIRMED),
        _booking("ended", "worker-1", BookingState.CONFIRMED),
    ]
    excluded[-1] = replace(excluded[-1], end_time=AT)
    for booking in [selected, earlier, *excluded]:
        shifts.save(_shift(booking.shift_id, booking.start_time, booking.end_time))
        bookings.save(booking)
    if session is not None:
        session.flush()
        session.expunge_all()

    result = bookings.list_live_for_workers(["worker-1", "worker-2"], AT)

    assert [booking.booking_id for booking in result] == ["earlier", "selected"]
    assert result[1] == selected
    assert bookings.list_live_for_workers([], AT) == []

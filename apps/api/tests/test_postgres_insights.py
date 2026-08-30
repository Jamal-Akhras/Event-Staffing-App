from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest

from apps.api.src.db.tenancy_models import OrganisationModel, VenueModel
from apps.api.src.models.application import Application
from apps.api.src.models.shift import Shift
from apps.api.src.repositories.sqlalchemy_application_repository import SqlAlchemyApplicationRepository
from apps.api.src.repositories.sqlalchemy_booking_repository import SqlAlchemyBookingRepository
from apps.api.src.repositories.sqlalchemy_shift_repository import SqlAlchemyShiftRepository
from packages.domain.src.booking import Booking
from packages.domain.src.booking_state import BookingState

pytestmark = pytest.mark.postgres

NOW = datetime(2030, 3, 12, 9, 0, tzinfo=UTC)
TODAY = NOW.replace(hour=0, minute=0, second=0, microsecond=0)
VENUE = "venue-insights"
COMPLETED_HISTORY = 12


def _shift(shifts, start: datetime, needed: int, filled: int, status: str) -> str:
    shift_id = str(uuid4())
    shifts.save(
        Shift(
            shift_id=shift_id,
            operator_id="operator-insights",
            account_id=VENUE,
            role="Bartender",
            location="Main bar",
            start_time=start,
            end_time=start + timedelta(hours=5),
            pay_rate=14,
            notes=None,
            status=status,
            created_at=TODAY - timedelta(days=90),
            workers_needed=needed,
            workers_filled=filled,
        )
    )
    return shift_id


def _booking(bookings, shift_id: str, worker_id: str, state: BookingState, start: datetime) -> None:
    bookings.save(
        Booking(
            booking_id=str(uuid4()),
            shift_id=shift_id,
            worker_id=worker_id,
            operator_id="operator-insights",
            start_time=start,
            end_time=start + timedelta(hours=5),
            state=state,
            created_at=start - timedelta(days=1),
        )
    )


def _seed() -> str:
    from apps.api.src.db.database import SessionLocal

    with SessionLocal() as session, session.begin():
        session.add(
            OrganisationModel(
                organisation_id="organisation-insights",
                name="Insights Org",
                country="GB",
                currency="GBP",
                created_at=NOW,
            )
        )
        session.add(
            VenueModel(
                venue_id=VENUE,
                organisation_id="organisation-insights",
                market_id="bath-gb",
                name="Insights Venue",
                country="GB",
                currency="GBP",
                created_at=NOW,
            )
        )
        session.flush()
        shifts = SqlAlchemyShiftRepository(session)
        bookings = SqlAlchemyBookingRepository(session)
        applications = SqlAlchemyApplicationRepository(session)

        today_shift = _shift(shifts, TODAY + timedelta(hours=18), needed=4, filled=1, status="open")
        _shift(shifts, TODAY + timedelta(days=3, hours=18), needed=5, filled=0, status="open")
        _shift(shifts, TODAY + timedelta(days=3, hours=18), needed=5, filled=0, status="cancelled")
        _shift(shifts, TODAY + timedelta(days=40, hours=18), needed=9, filled=0, status="open")

        for index in range(COMPLETED_HISTORY):
            start = NOW - timedelta(days=index + 1)
            _booking(bookings, _shift(shifts, start, 1, 1, "filled"), "worker-a", BookingState.PAID, start)

        old_start = NOW - timedelta(days=45)
        _booking(bookings, _shift(shifts, old_start, 1, 1, "filled"), "worker-a", BookingState.PAID, old_start)

        broken_start = NOW - timedelta(days=2)
        _booking(bookings, _shift(shifts, broken_start, 1, 0, "open"), "worker-b", BookingState.NO_SHOW, broken_start)
        _booking(bookings, today_shift, "worker-c", BookingState.CONFIRMED, TODAY + timedelta(hours=18))

        for index in range(3):
            applications.save(
                Application(
                    application_id=str(uuid4()),
                    shift_id=today_shift,
                    worker_id=f"worker-pending-{index}",
                    operator_id="operator-insights",
                    message=None,
                    status="applied",
                    created_at=NOW - timedelta(days=index + 1),
                    start_time=TODAY + timedelta(hours=18),
                    end_time=TODAY + timedelta(hours=23),
                    booking_id=None,
                )
            )
    return today_shift


def test_sql_aggregates_match_the_venue_history():
    from apps.api.src.db.database import SessionLocal

    today_shift = _seed()
    with SessionLocal() as session:
        shifts = SqlAlchemyShiftRepository(session)
        bookings = SqlAlchemyBookingRepository(session)
        applications = SqlAlchemyApplicationRepository(session)

        in_week = shifts.list_in_range(VENUE, TODAY, TODAY + timedelta(days=7))
        assert sorted(shift.status for shift in in_week) == ["cancelled", "open", "open"]

        attendance = bookings.attendance_summary(VENUE, NOW - timedelta(days=30), NOW)
        assert (attendance.completed, attendance.no_shows, attendance.total) == (COMPLETED_HISTORY, 1, 13)

        activity = {row.worker_id: row for row in bookings.worker_activity(VENUE, NOW - timedelta(days=90))}
        assert activity["worker-a"].completed == COMPLETED_HISTORY + 1
        assert activity["worker-a"].last_worked == NOW - timedelta(days=1)
        assert activity["worker-a"].recently_broken is False
        assert activity["worker-b"].completed == 0
        assert activity["worker-b"].recently_broken is True
        assert activity["worker-c"].completed == 0

        pending = applications.pending_summary(VENUE)
        assert pending.count == 3
        assert pending.oldest_created_at == NOW - timedelta(days=3)

        assert [booking.worker_id for booking in bookings.list_for_shifts([today_shift])] == ["worker-c"]

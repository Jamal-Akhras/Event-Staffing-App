from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from apps.api.src import main
from apps.api.src.deps import get_application_repo, get_booking_repo, get_shift_repo
from apps.api.src.models.application import Application
from apps.api.src.models.shift import Shift
from apps.api.src.repositories.in_memory_application_repository import InMemoryApplicationRepository
from apps.api.src.repositories.in_memory_booking_repository import InMemoryBookingRepository
from apps.api.src.repositories.in_memory_shift_repository import InMemoryShiftRepository
from packages.domain.src.booking import Booking
from packages.domain.src.booking_state import BookingState

VENUE = {"X-Actor-Role": "operator", "X-Actor-Id": "operator-1", "X-Account-Id": "venue-1"}
OTHER_VENUE = {"X-Actor-Role": "operator", "X-Actor-Id": "operator-2", "X-Account-Id": "venue-2"}
WORKER = {"X-Actor-Role": "worker", "X-Actor-Id": "worker-1"}
NOW = datetime(2030, 3, 12, 9, 0, tzinfo=UTC)
TODAY = NOW.replace(hour=0, minute=0, second=0, microsecond=0)


@pytest.fixture(autouse=True)
def freeze_clock(monkeypatch):
    monkeypatch.setattr("apps.api.src.routes.insights.utc_now", lambda: NOW)


def _shift(shifts, day_offset: int, needed: int, filled: int, account_id: str = "venue-1", status: str = "open"):
    shift_id = str(uuid4())
    shifts.save(
        Shift(
            shift_id=shift_id,
            operator_id="operator-1",
            account_id=account_id,
            role="Bartender",
            location="Main bar",
            start_time=TODAY + timedelta(days=day_offset, hours=18),
            end_time=TODAY + timedelta(days=day_offset, hours=23),
            pay_rate=14,
            notes=None,
            status=status,
            created_at=TODAY - timedelta(days=7),
            workers_needed=needed,
            workers_filled=filled,
        )
    )
    return shift_id


def _booking(bookings, shift_id: str, worker_id: str, state: BookingState, start: datetime):
    booking_id = str(uuid4())
    bookings.save(
        Booking(
            booking_id=booking_id,
            shift_id=shift_id,
            worker_id=worker_id,
            operator_id="operator-1",
            start_time=start,
            end_time=start + timedelta(hours=5),
            state=state,
            created_at=start - timedelta(days=1),
        )
    )
    return booking_id


def _client():
    bookings = InMemoryBookingRepository()
    shifts = InMemoryShiftRepository(bookings)
    bookings.attach_shift_repo(shifts)
    applications = InMemoryApplicationRepository()
    applications.attach_shift_repo(shifts)
    main.app.dependency_overrides[get_booking_repo] = lambda: bookings
    main.app.dependency_overrides[get_shift_repo] = lambda: shifts
    main.app.dependency_overrides[get_application_repo] = lambda: applications
    return TestClient(main.app), shifts, bookings, applications


def test_open_seats_are_counted_across_the_whole_week_not_a_page():
    client, shifts, _, _ = _client()
    for day in range(7):
        for _ in range(20):
            _shift(shifts, day, needed=3, filled=1)

    body = client.get("/insights/overview", headers=VENUE).json()
    assert len(body["days"]) == 7
    assert body["open_seats"] == 7 * 20 * 2
    assert all(day["total_shifts"] == 20 and day["open_seats"] == 40 for day in body["days"])


def test_coverage_ignores_cancelled_and_filled_shifts_and_other_venues():
    client, shifts, _, _ = _client()
    _shift(shifts, 0, needed=4, filled=1)
    _shift(shifts, 0, needed=4, filled=0, status="cancelled")
    _shift(shifts, 0, needed=4, filled=4, status="filled")
    _shift(shifts, 0, needed=9, filled=0, account_id="venue-2")

    body = client.get("/insights/overview", headers=VENUE).json()
    assert body["days"][0]["total_shifts"] == 2
    assert body["open_seats"] == 3
    assert client.get("/insights/overview", headers=OTHER_VENUE).json()["open_seats"] == 9


def test_pending_applications_count_everything_waiting():
    client, shifts, _, applications = _client()
    shift_id = _shift(shifts, 1, needed=1, filled=0)
    oldest = NOW - timedelta(days=3)
    for index in range(150):
        applications.save(
            Application(
                application_id=str(uuid4()),
                shift_id=shift_id,
                worker_id=f"worker-{index}",
                operator_id="operator-1",
                message=None,
                status="applied" if index < 149 else "approved",
                created_at=oldest + timedelta(minutes=index),
                start_time=TODAY + timedelta(days=1, hours=18),
                end_time=TODAY + timedelta(days=1, hours=23),
                booking_id=None,
            )
        )

    pending = client.get("/insights/overview", headers=VENUE).json()["pending_applications"]
    assert pending["count"] == 149
    assert pending["oldest_created_at"].startswith("2030-03-09T09:00")


def test_attendance_rate_uses_the_last_thirty_days():
    client, shifts, bookings, _ = _client()
    shift_id = _shift(shifts, 0, needed=1, filled=1)
    for _ in range(9):
        _booking(bookings, shift_id, "worker-1", BookingState.APPROVED, NOW - timedelta(days=5))
    _booking(bookings, shift_id, "worker-2", BookingState.NO_SHOW, NOW - timedelta(days=5))
    _booking(bookings, shift_id, "worker-3", BookingState.NO_SHOW, NOW - timedelta(days=60))

    attendance = client.get("/insights/overview", headers=VENUE).json()["attendance"]
    assert (attendance["completed"], attendance["no_shows"], attendance["total"]) == (9, 1, 10)
    assert attendance["rate"] == 90


def test_tonight_lists_todays_shifts_with_their_booked_workers():
    client, shifts, bookings, _ = _client()
    today_shift = _shift(shifts, 0, needed=3, filled=1)
    _shift(shifts, 2, needed=1, filled=0)
    _booking(bookings, today_shift, "worker-1", BookingState.CONFIRMED, TODAY + timedelta(hours=18))
    _booking(bookings, today_shift, "worker-2", BookingState.CANCELLED_BY_WORKER, TODAY + timedelta(hours=18))

    tonight = client.get("/insights/overview", headers=VENUE).json()["tonight"]
    assert len(tonight) == 1
    assert [worker["worker_id"] for worker in tonight[0]["workers"]] == ["worker-1"]
    assert tonight[0]["workers"][0]["check_in_code"]
    assert tonight[0]["missing"] == 2


def test_roster_activity_counts_all_history_per_worker():
    client, shifts, bookings, _ = _client()
    for index in range(120):
        worked = _shift(shifts, -(index + 1), needed=1, filled=1, status="filled")
        _booking(bookings, worked, "worker-1", BookingState.PAID, NOW - timedelta(days=index + 1))
    missed = _shift(shifts, -2, needed=1, filled=0)
    _booking(bookings, missed, "worker-2", BookingState.NO_SHOW, NOW - timedelta(days=2))

    workers = {row["worker_id"]: row for row in client.get("/insights/roster", headers=VENUE).json()["workers"]}
    assert workers["worker-1"]["completed"] == 120
    assert workers["worker-1"]["last_worked"].startswith("2030-03-11")
    assert workers["worker-1"]["recently_broken"] is False
    assert workers["worker-2"]["completed"] == 0
    assert workers["worker-2"]["recently_broken"] is True


def test_insights_require_an_operator_with_a_venue():
    client, _, _, _ = _client()
    assert client.get("/insights/overview", headers=WORKER).status_code == 403
    assert client.get("/insights/roster", headers=WORKER).status_code == 403
    assert client.get("/insights/overview").status_code == 401


def test_the_shift_range_accepts_the_windows_the_clients_ask_for():
    client, shifts, _, _ = _client()
    _shift(shifts, 1, needed=1, filled=0)

    operations = client.get(
        "/shifts",
        params={
            "starts_from": (TODAY - timedelta(days=30)).isoformat(),
            "starts_before": (TODAY + timedelta(days=92)).isoformat(),
        },
        headers=VENUE,
    )
    assert operations.status_code == 200

    history = client.get(
        "/shifts",
        params={
            "starts_from": (TODAY - timedelta(days=180)).isoformat(),
            "starts_before": (TODAY + timedelta(days=1)).isoformat(),
        },
        headers=VENUE,
    )
    assert history.status_code == 200

    too_wide = client.get(
        "/shifts",
        params={
            "starts_from": (TODAY - timedelta(days=200)).isoformat(),
            "starts_before": (TODAY + timedelta(days=1)).isoformat(),
        },
        headers=VENUE,
    )
    assert too_wide.status_code == 400


def test_analytics_counts_every_shift_not_just_a_page():
    client, shifts, bookings, applications = _client()
    for index in range(60):
        shift_id = _shift(shifts, -(index % 20) - 1, needed=2, filled=2 if index % 3 else 1, status="filled")
        applications.save(
            Application(
                application_id=str(uuid4()),
                shift_id=shift_id,
                worker_id=f"worker-{index}",
                operator_id="operator-1",
                message=None,
                status="applied",
                created_at=NOW - timedelta(days=2),
                start_time=TODAY,
                end_time=TODAY + timedelta(hours=5),
                booking_id=None,
            )
        )

    body = client.get("/insights/analytics?period=month", headers=VENUE).json()
    assert body["seats_posted"] == 120
    assert body["applications"] == 60
    assert len(body["fill_rate_trend"]) == 6
    assert body["roles"][0]["seats"] == 120


def test_analytics_names_the_seats_that_went_unfilled():
    client, shifts, _, applications = _client()
    short = _shift(shifts, -3, needed=4, filled=1, status="open")
    _shift(shifts, -2, needed=2, filled=2, status="filled")
    applications.save(
        Application(
            application_id=str(uuid4()),
            shift_id=short,
            worker_id="worker-9",
            operator_id="operator-1",
            message=None,
            status="applied",
            created_at=NOW - timedelta(days=4),
            start_time=TODAY,
            end_time=TODAY + timedelta(hours=5),
            booking_id=None,
        )
    )

    body = client.get("/insights/analytics?period=month", headers=VENUE).json()
    assert len(body["gaps"]) == 1
    gap = body["gaps"][0]
    assert gap["unfilled"] == 3
    assert gap["applications"] == 1
    assert gap["reason"]


def test_analytics_ignores_future_shifts_when_reporting_gaps():
    client, shifts, _, _ = _client()
    _shift(shifts, 5, needed=4, filled=0, status="open")

    body = client.get("/insights/analytics?period=month", headers=VENUE).json()
    assert body["gaps"] == []


def test_a_shift_posted_after_it_started_does_not_report_negative_lead():
    client, shifts, _, _ = _client()
    shift_id = str(uuid4())
    start = TODAY - timedelta(days=2)
    shifts.save(
        Shift(
            shift_id=shift_id,
            operator_id="operator-1",
            account_id="venue-1",
            role="Bartender",
            location="Main bar",
            start_time=start,
            end_time=start + timedelta(hours=5),
            pay_rate=14,
            notes=None,
            status="open",
            created_at=start + timedelta(hours=3),
            workers_needed=2,
            workers_filled=0,
        )
    )

    gap = client.get("/insights/analytics?period=month", headers=VENUE).json()["gaps"][0]
    assert "-" not in gap["reason"]
    assert gap["reason"] == "Posted less than an hour ahead"

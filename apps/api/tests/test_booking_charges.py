from dataclasses import replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient

from apps.api.src import main
from apps.api.src.deps import (
    get_booking_charge_repo,
    get_booking_repo,
    get_booking_transition_repo,
    get_partner_code_repo,
    get_shift_repo,
    get_worker_profile_repo,
)
from apps.api.src.models.shift import Shift
from apps.api.src.models.worker_profile import WorkerProfile
from apps.api.src.repositories.in_memory_booking_repository import InMemoryBookingRepository
from apps.api.src.repositories.in_memory_partner_code_repository import InMemoryPartnerCodeRepository
from apps.api.src.repositories.in_memory_shift_repository import InMemoryShiftRepository
from apps.api.src.repositories.in_memory_worker_profile_repository import InMemoryWorkerProfileRepository
from apps.api.src.repository_dependencies import (
    shared_booking_charge_repository,
    shared_booking_transition_repository,
    shared_event_repository,
)
from packages.domain.src.booking import Booking
from packages.domain.src.booking_state import BookingState

VENUE = {"X-Actor-Role": "operator", "X-Actor-Id": "operator-1", "X-Account-Id": "venue-1"}
CREATED = datetime(2030, 3, 1, tzinfo=UTC)
START = datetime(2030, 3, 12, 18, 0, tzinfo=UTC)
APPROVED_AT = START + timedelta(hours=6)
CODE = "4821"


@pytest.fixture(autouse=True)
def clear_state():
    shared_booking_charge_repository().clear()
    shared_booking_transition_repository().clear()
    shared_event_repository().clear()
    yield
    shared_booking_charge_repository().clear()
    shared_booking_transition_repository().clear()
    shared_event_repository().clear()


def _client():
    bookings = InMemoryBookingRepository()
    shifts = InMemoryShiftRepository(bookings)
    bookings.attach_shift_repo(shifts)
    workers = InMemoryWorkerProfileRepository()
    shift = Shift(
        shift_id="shift-1",
        operator_id="operator-1",
        account_id="venue-1",
        role="Bartender",
        location="Main bar",
        start_time=START,
        end_time=START + timedelta(hours=5),
        pay_rate=Decimal("14.50"),
        notes=None,
        status="filled",
        created_at=CREATED,
        workers_needed=1,
        workers_filled=1,
    )
    shifts.save(shift)
    workers.save(
        WorkerProfile(
            worker_id="worker-1",
            display_name="Alex Worker",
            role="Bartender",
            city="Bath",
            experience_years=3,
            reliability_score=1.0,
            badges=[],
            bio=None,
            languages=["en"],
            email=None,
            phone=None,
            address=None,
            emergency_contact=None,
            pay_rate=None,
            notes=None,
            updated_at=CREATED,
        )
    )
    bookings.save(
        Booking(
            booking_id="bk-1",
            shift_id="shift-1",
            worker_id="worker-1",
            operator_id="operator-1",
            start_time=shift.start_time,
            end_time=shift.end_time,
            state=BookingState.CHECKED_OUT,
            created_at=CREATED,
            confirmed_at=CREATED,
            checked_in_at=shift.start_time,
            checked_out_at=shift.end_time,
            completion_code=CODE,
        )
    )
    main.app.dependency_overrides[get_booking_repo] = lambda: bookings
    main.app.dependency_overrides[get_shift_repo] = lambda: shifts
    main.app.dependency_overrides[get_worker_profile_repo] = lambda: workers
    main.app.dependency_overrides[get_partner_code_repo] = InMemoryPartnerCodeRepository
    main.app.dependency_overrides[get_booking_transition_repo] = shared_booking_transition_repository
    main.app.dependency_overrides[get_booking_charge_repo] = shared_booking_charge_repository
    return TestClient(main.app), shifts, workers, shift


def _approve(client: TestClient, booking_id: str = "bk-1") -> None:
    response = client.post(
        f"/bookings/{booking_id}/approve",
        json={"code": CODE, "now": APPROVED_AT.isoformat()},
        headers=VENUE,
    )
    assert response.status_code == 200, response.text


def _line(client: TestClient) -> dict:
    body = client.get("/billing/summary?month=2030-03", headers=VENUE).json()
    assert len(body["lines"]) == 1
    return body["lines"][0]


def test_approval_freezes_the_charge_from_the_rate_at_the_time():
    client, _, _, _ = _client()
    _approve(client)
    line = _line(client)
    assert (line["hours"], line["wages"], line["fee"], line["total"]) == ("5.00", "72.50", "5.80", "78.30")


def test_raising_the_shift_rate_afterwards_does_not_rewrite_the_invoice():
    client, shifts, _, shift = _client()
    _approve(client)
    before = _line(client)

    shifts.save(replace(shift, pay_rate=Decimal("30.00")))

    assert _line(client) == before


def test_renaming_the_worker_afterwards_does_not_rewrite_the_invoice():
    client, _, workers, _ = _client()
    _approve(client)
    assert _line(client)["worker_name"] == "Alex Worker"

    profile = workers.get("worker-1")
    workers.save(replace(profile, display_name="Alexandra Worker"))

    assert _line(client)["worker_name"] == "Alex Worker"


def test_approving_twice_charges_once_and_records_one_transition():
    client, _, _, _ = _client()
    _approve(client)
    _approve(client)

    assert len(shared_booking_charge_repository().list_for_account("venue-1")) == 1
    history = client.get("/bookings/bk-1/transitions", headers=VENUE).json()
    assert [item["to_state"] for item in history] == ["approved"]


def test_the_frozen_charge_is_recorded_in_the_event_log():
    client, _, _, _ = _client()
    _approve(client)
    events = client.get(
        "/system/events",
        params={"name": "billing.charge_frozen", "limit": 10},
        headers={"X-Actor-Role": "system", "X-Actor-Id": "system"},
    ).json()["events"]
    assert len(events) == 1
    assert events[0]["context"]["wages"] == "72.50"
    assert events[0]["context"]["fee"] == "5.80"
    assert events[0]["context"]["fee_waived"] is False


def test_worker_earnings_come_from_the_frozen_charge():
    client, shifts, _, shift = _client()
    _approve(client)
    worker = {"X-Actor-Role": "worker", "X-Actor-Id": "worker-1"}

    before = client.get("/workers/worker-1/earnings?period=year", headers=worker).json()
    assert before["entries"][0]["total"] == "72.50"
    assert before["entries"][0]["hours"] == 5.0
    assert before["entries"][0]["frozen"] is True

    shifts.save(replace(shift, pay_rate=Decimal("30.00")))

    after = client.get("/workers/worker-1/earnings?period=year", headers=worker).json()
    assert after["entries"][0]["total"] == "72.50"
    assert after["total_pending"] == before["total_pending"]

import os
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
from apps.api.src.models.partner_code import PartnerCode
from apps.api.src.models.shift import Shift
from apps.api.src.repositories.in_memory_booking_repository import InMemoryBookingRepository
from apps.api.src.repositories.in_memory_partner_code_repository import InMemoryPartnerCodeRepository
from apps.api.src.repositories.in_memory_shift_repository import InMemoryShiftRepository
from apps.api.src.repositories.in_memory_worker_profile_repository import InMemoryWorkerProfileRepository
from apps.api.src.repository_dependencies import (
    shared_booking_charge_repository,
    shared_booking_transition_repository,
)
from apps.api.src.services.billing_service import new_partner_code
from packages.domain.src.booking import Booking
from packages.domain.src.booking_state import BookingState

os.environ["PLATFORM_FEE_PERCENT"] = "8"

VENUE = {"X-Actor-Role": "operator", "X-Actor-Id": "operator-1", "X-Account-Id": "venue-1"}
OTHER_VENUE = {"X-Actor-Role": "operator", "X-Actor-Id": "operator-2", "X-Account-Id": "venue-2"}
WORKER = {"X-Actor-Role": "worker", "X-Actor-Id": "worker-1"}
START = datetime(2030, 3, 12, 18, 0, tzinfo=UTC)
CREATED = datetime(2030, 3, 1, tzinfo=UTC)
APPROVED_AT = START + timedelta(hours=6)


@pytest.fixture(autouse=True)
def freeze_billing_clock(monkeypatch):
    monkeypatch.setattr("apps.api.src.routes.billing.utc_now", lambda: CREATED)


@pytest.fixture(autouse=True)
def clear_charges():
    shared_booking_charge_repository().clear()
    yield
    shared_booking_charge_repository().clear()


def _shift(shift_id: str, start: datetime) -> Shift:
    return Shift(
        shift_id=shift_id,
        operator_id="operator-1",
        account_id="venue-1",
        role="Bartender",
        location="Main bar",
        start_time=start,
        end_time=start + timedelta(hours=5),
        pay_rate=Decimal("14.50"),
        notes=None,
        status="filled",
        created_at=CREATED,
        workers_needed=1,
        workers_filled=1,
    )


def _worked(booking_id: str, shift: Shift, worker_id: str = "worker-1") -> Booking:
    return Booking(
        booking_id=booking_id,
        shift_id=shift.shift_id,
        worker_id=worker_id,
        operator_id="operator-1",
        start_time=shift.start_time,
        end_time=shift.end_time,
        state=BookingState.CHECKED_OUT,
        created_at=CREATED,
        confirmed_at=CREATED,
        checked_in_at=shift.start_time,
        checked_out_at=shift.end_time,
        completion_code="4821",
    )


def _approve(client: TestClient, booking_id: str, approved_at: datetime) -> None:
    response = client.post(
        f"/bookings/{booking_id}/approve",
        json={"code": "4821", "now": approved_at.isoformat()},
        headers=VENUE,
    )
    assert response.status_code == 200, response.text


def _client(extra_completed: int = 0):
    bookings = InMemoryBookingRepository()
    shifts = InMemoryShiftRepository(bookings)
    bookings.attach_shift_repo(shifts)
    codes = InMemoryPartnerCodeRepository()
    workers = InMemoryWorkerProfileRepository()

    first = _shift("shift-1", START)
    shifts.save(first)
    bookings.save(_worked("bk-1", first))
    bookings.save(
        Booking(
            booking_id="bk-open",
            shift_id="shift-1",
            worker_id="worker-2",
            operator_id="operator-1",
            start_time=first.start_time,
            end_time=first.end_time,
            state=BookingState.CONFIRMED,
            created_at=CREATED,
            confirmed_at=CREATED,
        )
    )
    for index in range(extra_completed):
        shift = _shift(f"shift-{index + 2}", START + timedelta(days=index + 1))
        shifts.save(shift)
        bookings.save(_worked(f"bk-{index + 2}", shift))

    main.app.dependency_overrides[get_booking_repo] = lambda: bookings
    main.app.dependency_overrides[get_booking_transition_repo] = shared_booking_transition_repository
    main.app.dependency_overrides[get_booking_charge_repo] = shared_booking_charge_repository
    main.app.dependency_overrides[get_shift_repo] = lambda: shifts
    main.app.dependency_overrides[get_worker_profile_repo] = lambda: workers
    main.app.dependency_overrides[get_partner_code_repo] = lambda: codes
    return TestClient(main.app), codes


def _code(code: str, shift_cap: int = 20, max_redemptions: int = 1, expires_at: datetime | None = None) -> PartnerCode:
    return PartnerCode(
        code=code,
        label="Bath founding ten",
        waiver_months=3,
        shift_cap=shift_cap,
        max_redemptions=max_redemptions,
        created_at=CREATED,
        created_by="founder",
        expires_at=expires_at,
    )


def test_summary_charges_fee_on_completed_bookings_only():
    client, _ = _client()
    _approve(client, "bk-1", APPROVED_AT)
    response = client.get("/billing/summary?month=2030-03", headers=VENUE)
    assert response.status_code == 200
    body = response.json()
    assert body["plan"] == "standard"
    assert body["fee_percent"] == "8"
    assert [line["booking_id"] for line in body["lines"]] == ["bk-1"]
    line = body["lines"][0]
    assert (line["hours"], line["wages"], line["fee"], line["total"]) == ("5.00", "72.50", "5.80", "78.30")
    assert line["waived"] is False
    assert (body["wages_total"], body["fee_total"], body["grand_total"]) == ("72.50", "5.80", "78.30")
    assert body["completed_shifts_all_time"] == 1


def test_summary_is_scoped_to_month_and_venue():
    client, _ = _client()
    _approve(client, "bk-1", APPROVED_AT)
    assert client.get("/billing/summary?month=2030-04", headers=VENUE).json()["lines"] == []
    assert client.get("/billing/summary?month=2030-03", headers=OTHER_VENUE).json()["lines"] == []
    assert client.get("/billing/summary", headers=WORKER).status_code == 403


def test_redeeming_a_partner_code_waives_the_fee():
    client, codes = _client()
    codes.save_code(_code("BATH-TEST-CODE"))
    response = client.post("/billing/partner-codes/redeem", json={"code": "bath-test-code"}, headers=VENUE)
    assert response.status_code == 200
    assert response.json()["active"] is True
    _approve(client, "bk-1", APPROVED_AT)
    body = client.get("/billing/summary?month=2030-03", headers=VENUE).json()
    assert body["plan"] == "founding_partner"
    assert body["lines"][0]["waived"] is True
    assert body["lines"][0]["fee"] == "0.00"
    assert body["fee_total"] == "0.00"
    assert body["waiver"]["shifts_used"] == 1
    assert body["waiver"]["shift_cap"] == 20
    assert body["waiver"]["fee_waived_until"].startswith("2030-06-01")


def test_partner_code_rejections():
    client, codes = _client()
    codes.save_code(_code("BATH-ONCE-ONLY"))
    codes.save_code(_code("BATH-OLD-CODE", expires_at=datetime(2020, 1, 1, tzinfo=UTC)))
    assert client.post("/billing/partner-codes/redeem", json={"code": "BATH-NOPE"}, headers=VENUE).status_code == 404
    assert client.post("/billing/partner-codes/redeem", json={"code": "BATH-OLD-CODE"}, headers=VENUE).status_code == 400
    assert client.post("/billing/partner-codes/redeem", json={"code": "BATH-ONCE-ONLY"}, headers=VENUE).status_code == 200
    assert client.post("/billing/partner-codes/redeem", json={"code": "BATH-ONCE-ONLY"}, headers=VENUE).status_code == 409
    assert client.post("/billing/partner-codes/redeem", json={"code": "BATH-ONCE-ONLY"}, headers=OTHER_VENUE).status_code == 409


def test_waiver_stops_at_the_shift_cap():
    client, codes = _client(extra_completed=1)
    codes.save_code(_code("BATH-CAP-ONE", shift_cap=1))
    client.post("/billing/partner-codes/redeem", json={"code": "BATH-CAP-ONE"}, headers=VENUE)
    _approve(client, "bk-1", APPROVED_AT)
    _approve(client, "bk-2", APPROVED_AT + timedelta(days=1))
    body = client.get("/billing/summary?month=2030-03", headers=VENUE).json()
    assert [line["waived"] for line in body["lines"]] == [True, False]
    assert body["fee_total"] == "5.80"
    assert body["waiver"]["active"] is False
    assert body["plan"] == "standard"


def test_new_founding_code_has_fixed_three_month_twenty_shift_terms():
    code = new_partner_code(
        prefix="bath",
        label="Bath founding partner",
        max_redemptions=1,
        created_by="founder",
        now=CREATED,
        expires_at=CREATED + timedelta(days=30),
    )

    assert code.waiver_months == 3
    assert code.shift_cap == 20

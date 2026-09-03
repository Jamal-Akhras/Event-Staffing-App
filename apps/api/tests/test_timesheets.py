from datetime import UTC, date, datetime, timedelta
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient

from apps.api.src import main
from apps.api.src.models.account import Account
from apps.api.src.models.booking_charge import BookingCharge
from apps.api.src.models.shift import Shift
from apps.api.src.models.worker_profile import WorkerProfile
from apps.api.src.models.worker_relationship import WorkerRelationship
from apps.api.src.repository_dependencies import (
    get_account_repo,
    get_booking_repo,
    get_shift_repo,
    get_worker_profile_repo,
    shared_booking_charge_adjustment_repository,
    shared_booking_charge_repository,
    shared_booking_transition_repository,
)
from apps.api.src.repository_dependencies_workforce import (
    shared_relationship_transition_repository,
    shared_worker_relationship_repository,
)
from apps.api.src.services.booking_ops import sweep_no_shows
from packages.domain.src.booking import Booking
from packages.domain.src.booking_state import BookingState

VENUE_ID = "venue-1"
NOW = datetime(2030, 6, 3, 9, 0, tzinfo=UTC)
WEEK_START = date(2030, 6, 10)
START = datetime(2030, 6, 10, 18, 0, tzinfo=UTC)
END = START + timedelta(hours=5)
AFTER = END + timedelta(hours=2)
OPERATOR = {"X-Actor-Role": "operator", "X-Actor-Id": "operator-1", "X-Account-Id": VENUE_ID}
STAFF = {"X-Actor-Role": "worker", "X-Actor-Id": "staff-1"}
TEMP = {"X-Actor-Role": "worker", "X-Actor-Id": "temp-1"}


@pytest.fixture(autouse=True)
def clear_state():
    repos = (
        shared_booking_charge_repository(),
        shared_booking_charge_adjustment_repository(),
        shared_booking_transition_repository(),
        shared_worker_relationship_repository(),
        shared_relationship_transition_repository(),
    )
    for repo in repos:
        repo.clear()
    yield
    for repo in repos:
        repo.clear()


@pytest.fixture()
def client(in_memory_repos):
    in_memory_repos[get_account_repo].save(
        Account(
            account_id=VENUE_ID, name="The Grapes", country="GB", currency="GBP",
            created_at=NOW, market_id="bath-gb",
        )
    )
    for worker_id in ("staff-1", "temp-1"):
        in_memory_repos[get_worker_profile_repo].save(
            WorkerProfile(
                worker_id=worker_id, display_name=worker_id, role="Bartender", city="Bath",
                experience_years=1, reliability_score=1.0, badges=[], bio=None, languages=["en"],
                email=None, phone=None, address=None, emergency_contact=None, pay_rate=None,
                notes=None, updated_at=NOW, market_id="bath-gb",
            )
        )
    shared_worker_relationship_repository().save(
        WorkerRelationship(
            relationship_id="rel-staff-1",
            venue_id=VENUE_ID,
            worker_id="staff-1",
            relationship_type="permanent",
            status="active",
            created_at=NOW,
            updated_at=NOW,
            contracted_hours_per_week=Decimal("20.00"),
        )
    )
    return TestClient(main.app)


def _shift(
    repos, shift_id: str, start: datetime = START, hours: int = 5,
    account_id: str = VENUE_ID, role: str = "Bartender",
) -> Shift:
    shift = Shift(
        shift_id=shift_id,
        operator_id="operator-1",
        account_id=account_id,
        role=role,
        location="Main bar",
        start_time=start,
        end_time=start + timedelta(hours=hours),
        pay_rate=Decimal("14.50"),
        notes=None,
        status="filled",
        created_at=NOW,
        workers_needed=1,
        workers_filled=1,
    )
    repos[get_shift_repo].save(shift)
    return shift


def _booking(
    repos, booking_id: str, shift: Shift, worker_id: str, state: BookingState,
    attendance_mode: str = "pin", clocked: bool = False,
) -> Booking:
    booking = Booking(
        booking_id=booking_id,
        shift_id=shift.shift_id,
        worker_id=worker_id,
        operator_id="operator-1",
        start_time=shift.start_time,
        end_time=shift.end_time,
        state=state,
        created_at=NOW,
        confirmed_at=NOW,
        checked_in_at=shift.start_time if clocked else None,
        checked_out_at=shift.end_time if clocked else None,
        check_in_code="1234",
        completion_code="4821",
        attendance_mode=attendance_mode,
    )
    repos[get_booking_repo].save(booking)
    return booking


def _seed_charge(
    booking: Booking, charge_id: str, fee_percent: str = "8.00", fee: str = "5.80",
    fee_waived: bool = False,
) -> BookingCharge:
    return shared_booking_charge_repository().record(
        BookingCharge(
            charge_id=charge_id,
            booking_id=booking.booking_id,
            shift_id=booking.shift_id,
            account_id=VENUE_ID,
            worker_id=booking.worker_id,
            worker_name=booking.worker_id,
            role="Bartender",
            period="2030-06",
            start_time=booking.start_time,
            end_time=booking.end_time,
            completed_at=booking.end_time,
            hours=Decimal("5.00"),
            pay_rate=Decimal("14.50"),
            wages=Decimal("72.50"),
            fee_percent=Decimal(fee_percent),
            fee=Decimal(fee),
            total=Decimal("72.50") + Decimal(fee),
            currency="GBP",
            fee_waived=fee_waived,
            waiver_code="PARTNER" if fee_waived else None,
            recorded_at=booking.end_time,
            worker_relationship="one_off",
        )
    )


def test_an_employed_booking_checks_in_without_a_code(client, in_memory_repos):
    shift = _shift(in_memory_repos, "shift-1")
    _booking(in_memory_repos, "bk-1", shift, "staff-1", BookingState.CONFIRMED, "employed")

    response = client.post(
        "/bookings/bk-1/check-in", json={"now": START.isoformat()}, headers=STAFF
    )
    assert response.status_code == 200, response.text
    assert response.json()["state"] == "checked_in"


def test_a_temp_needs_the_code_even_after_a_promotion(client, in_memory_repos):
    shift = _shift(in_memory_repos, "shift-1")
    _booking(in_memory_repos, "bk-1", shift, "temp-1", BookingState.CONFIRMED, "pin")
    shared_worker_relationship_repository().save(
        WorkerRelationship(
            relationship_id="rel-temp-1",
            venue_id=VENUE_ID,
            worker_id="temp-1",
            relationship_type="permanent",
            status="active",
            created_at=NOW,
            updated_at=NOW,
        )
    )

    refused = client.post("/bookings/bk-1/check-in", json={"now": START.isoformat()}, headers=TEMP)
    assert refused.status_code == 400
    accepted = client.post(
        "/bookings/bk-1/check-in", json={"code": "1234", "now": START.isoformat()}, headers=TEMP
    )
    assert accepted.status_code == 200, accepted.text


def test_the_sweep_skips_employed_bookings_then_attendance_and_approval_land(client, in_memory_repos):
    employed_shift = _shift(in_memory_repos, "shift-emp")
    temp_shift = _shift(in_memory_repos, "shift-temp", start=START + timedelta(minutes=5))
    _booking(in_memory_repos, "bk-emp", employed_shift, "staff-1", BookingState.CONFIRMED, "employed")
    _booking(in_memory_repos, "bk-temp", temp_shift, "temp-1", BookingState.CONFIRMED, "pin")

    swept = sweep_no_shows(
        in_memory_repos[get_booking_repo],
        in_memory_repos[get_worker_profile_repo],
        in_memory_repos[get_shift_repo],
        START + timedelta(hours=2),
    )
    assert [b.booking_id for b in swept] == ["bk-temp"]
    assert in_memory_repos[get_booking_repo].get("bk-emp").state == BookingState.CONFIRMED

    recorded = client.post(
        "/venues/me/timesheet/bookings/bk-emp/attendance",
        json={
            "checked_in_at": START.isoformat(),
            "checked_out_at": (END + timedelta(minutes=15)).isoformat(),
            "now": AFTER.isoformat(),
        },
        headers=OPERATOR,
    )
    assert recorded.status_code == 200, recorded.text
    booking = in_memory_repos[get_booking_repo].get("bk-emp")
    assert booking.state == BookingState.CHECKED_OUT
    transitions = shared_booking_transition_repository().list_for_booking("bk-emp")
    assert [t.reason_code for t in transitions] == ["venue_recorded"]

    approved = client.post(
        "/venues/me/timesheet/approve",
        json={"booking_ids": ["bk-emp"], "now": AFTER.isoformat()},
        headers=OPERATOR,
    )
    assert approved.status_code == 200, approved.text
    assert approved.json()["results"] == [{"booking_id": "bk-emp", "result": "approved"}]
    charge = shared_booking_charge_repository().get_for_booking("bk-emp")
    assert charge.hours == Decimal("5.25")
    assert (charge.fee, charge.fee_percent) == (Decimal("0.00"), Decimal("0.00"))
    assert charge.worker_relationship == "permanent"


def test_attendance_recording_is_for_employed_confirmed_bookings_only(client, in_memory_repos):
    shift = _shift(in_memory_repos, "shift-1")
    _booking(in_memory_repos, "bk-pin", shift, "temp-1", BookingState.CONFIRMED, "pin")
    body = {
        "checked_in_at": START.isoformat(),
        "checked_out_at": END.isoformat(),
        "now": AFTER.isoformat(),
    }

    refused = client.post("/venues/me/timesheet/bookings/bk-pin/attendance", json=body, headers=OPERATOR)
    assert refused.status_code == 400
    assert "two-party codes" in refused.text

    other = _shift(in_memory_repos, "shift-2", start=START + timedelta(days=1))
    _booking(in_memory_repos, "bk-done", other, "staff-1", BookingState.CHECKED_OUT, "employed", clocked=True)
    late = client.post("/venues/me/timesheet/bookings/bk-done/attendance", json=body, headers=OPERATOR)
    assert late.status_code == 400


def test_adjusting_hours_guards_and_records_a_transition(client, in_memory_repos):
    shift = _shift(in_memory_repos, "shift-1")
    _booking(in_memory_repos, "bk-1", shift, "temp-1", BookingState.CHECKED_OUT, clocked=True)
    body = {
        "checked_in_at": (START + timedelta(minutes=30)).isoformat(),
        "checked_out_at": END.isoformat(),
        "reason": "Arrived late after bus strike",
        "now": AFTER.isoformat(),
    }

    response = client.post("/venues/me/timesheet/bookings/bk-1/adjust", json=body, headers=OPERATOR)
    assert response.status_code == 200, response.text
    booking = in_memory_repos[get_booking_repo].get("bk-1")
    assert booking.override_checked_in_at == START + timedelta(minutes=30)
    assert booking.checked_in_at == START
    transitions = shared_booking_transition_repository().list_for_booking("bk-1")
    assert [t.reason_code for t in transitions] == ["hours_adjusted"]
    assert transitions[0].context["previous_hours"] == "5.00"
    assert transitions[0].context["hours"] == "4.50"

    view = client.get(
        "/venues/me/timesheet", params={"week_start": WEEK_START.isoformat()}, headers=OPERATOR
    ).json()
    day = view["workers"][0]["days"][0]
    assert (day["hours_source"], day["worked_hours"]) == ("adjusted", "4.50")


def test_hours_cannot_be_adjusted_before_checkout_or_after_approval(client, in_memory_repos):
    shift = _shift(in_memory_repos, "shift-1")
    _booking(in_memory_repos, "bk-open", shift, "temp-1", BookingState.CONFIRMED)
    body = {
        "checked_in_at": START.isoformat(),
        "checked_out_at": END.isoformat(),
        "reason": "Testing the guard rails",
        "now": AFTER.isoformat(),
    }

    early = client.post("/venues/me/timesheet/bookings/bk-open/adjust", json=body, headers=OPERATOR)
    assert early.status_code == 400
    assert "checked out" in early.text

    backwards = client.post(
        "/venues/me/timesheet/bookings/bk-open/adjust",
        json={**body, "checked_out_at": (START - timedelta(hours=1)).isoformat()},
        headers=OPERATOR,
    )
    assert backwards.status_code == 400

    other = _shift(in_memory_repos, "shift-2", start=START + timedelta(days=1))
    approved = _booking(in_memory_repos, "bk-approved", other, "staff-1", BookingState.APPROVED, clocked=True)
    _seed_charge(approved, "charge-1")
    frozen = client.post("/venues/me/timesheet/bookings/bk-approved/adjust", json=body, headers=OPERATOR)
    assert frozen.status_code == 400
    assert "correct the charge" in frozen.text


def test_bulk_approval_returns_a_stable_code_per_row(client, in_memory_repos):
    ready = _shift(in_memory_repos, "shift-ready")
    _booking(in_memory_repos, "bk-ready", ready, "staff-1", BookingState.CHECKED_OUT, "employed", clocked=True)
    temp = _shift(in_memory_repos, "shift-temp", start=START + timedelta(days=1))
    _booking(in_memory_repos, "bk-temp", temp, "temp-1", BookingState.CHECKED_OUT, "pin", clocked=True)
    confirmed = _shift(in_memory_repos, "shift-conf", start=START + timedelta(days=2))
    _booking(in_memory_repos, "bk-conf", confirmed, "staff-1", BookingState.CONFIRMED, "employed")
    done = _shift(in_memory_repos, "shift-done", start=START + timedelta(days=3))
    _booking(in_memory_repos, "bk-done", done, "staff-1", BookingState.APPROVED, "employed", clocked=True)
    foreign = _shift(in_memory_repos, "shift-foreign", account_id="venue-2")
    _booking(in_memory_repos, "bk-foreign", foreign, "temp-1", BookingState.CHECKED_OUT, clocked=True)

    response = client.post(
        "/venues/me/timesheet/approve",
        json={
            "booking_ids": [
                "bk-ready", "bk-ready", "bk-temp", "bk-conf", "bk-done", "bk-foreign", "bk-missing",
            ],
            "now": AFTER.isoformat(),
        },
        headers=OPERATOR,
    )
    assert response.status_code == 200, response.text
    assert response.json()["results"] == [
        {"booking_id": "bk-ready", "result": "approved"},
        {"booking_id": "bk-temp", "result": "needs_worker_code"},
        {"booking_id": "bk-conf", "result": "not_approvable_state"},
        {"booking_id": "bk-done", "result": "already_approved"},
        {"booking_id": "bk-foreign", "result": "not_found"},
        {"booking_id": "bk-missing", "result": "not_found"},
    ]
    assert shared_booking_charge_repository().get_for_booking("bk-ready") is not None
    assert shared_booking_charge_repository().get_for_booking("bk-temp") is None

    overflow = client.post(
        "/venues/me/timesheet/approve",
        json={"booking_ids": [f"bk-{i}" for i in range(101)]},
        headers=OPERATOR,
    )
    assert overflow.status_code == 422


def test_bulk_approval_replays_under_the_same_key_and_reports_already_approved_fresh(client, in_memory_repos):
    from apps.api.src.config import use_in_memory_repositories

    if not use_in_memory_repositories():
        from apps.api.src.db.database import SessionLocal
        from apps.api.src.db.models import UserModel

        with SessionLocal() as session, session.begin():
            session.add(
                UserModel(
                    user_id="operator-1",
                    email="timesheet-idem@example.com",
                    hashed_password="x",
                    role="operator",
                    is_active=True,
                    created_at=NOW,
                    updated_at=NOW,
                    email_verified=True,
                )
            )
    shift = _shift(in_memory_repos, "shift-1")
    _booking(in_memory_repos, "bk-1", shift, "staff-1", BookingState.CHECKED_OUT, "employed", clocked=True)
    body = {"booking_ids": ["bk-1"], "now": AFTER.isoformat()}
    headers = {**OPERATOR, "Idempotency-Key": "approve-1"}

    first = client.post("/venues/me/timesheet/approve", json=body, headers=headers)
    assert first.json()["results"][0]["result"] == "approved"

    replay = client.post("/venues/me/timesheet/approve", json=body, headers=headers)
    assert replay.json() == first.json()
    assert len(shared_booking_charge_repository().list_for_account(VENUE_ID)) == 1

    fresh = client.post("/venues/me/timesheet/approve", json=body, headers=OPERATOR)
    assert fresh.json()["results"][0]["result"] == "already_approved"


def test_corrections_derive_money_server_side_and_render_in_the_view(client, in_memory_repos):
    shift = _shift(in_memory_repos, "shift-1")
    booking = _booking(in_memory_repos, "bk-1", shift, "temp-1", BookingState.APPROVED, clocked=True)
    _seed_charge(booking, "charge-1")

    response = client.post(
        "/venues/me/timesheet/charges/charge-1/correct",
        json={"delta_hours": "1.00", "reason": "Stayed for close-down", "now": AFTER.isoformat()},
        headers=OPERATOR,
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert (body["delta_wages"], body["delta_fee"]) == ("14.50", "1.16")

    view = client.get(
        "/venues/me/timesheet", params={"week_start": WEEK_START.isoformat()}, headers=OPERATOR
    ).json()
    day = view["workers"][0]["days"][0]
    assert (day["approved_hours"], day["approved_wages"]) == ("6.00", "87.00")
    assert day["adjustments_total_hours"] == "1.00"


def test_corrections_preserve_zero_fee_and_reject_negative_totals(client, in_memory_repos):
    shift = _shift(in_memory_repos, "shift-1")
    waived = _booking(in_memory_repos, "bk-waived", shift, "temp-1", BookingState.APPROVED, clocked=True)
    _seed_charge(waived, "charge-waived", fee="0.00", fee_waived=True)
    exempt_shift = _shift(in_memory_repos, "shift-2", start=START + timedelta(days=1))
    exempt = _booking(in_memory_repos, "bk-exempt", exempt_shift, "staff-1", BookingState.APPROVED, "employed", clocked=True)
    _seed_charge(exempt, "charge-exempt", fee_percent="0.00", fee="0.00")

    for charge_id in ("charge-waived", "charge-exempt"):
        response = client.post(
            f"/venues/me/timesheet/charges/{charge_id}/correct",
            json={"delta_hours": "1.00", "reason": "Stayed for close-down"},
            headers=OPERATOR,
        )
        assert response.status_code == 200, response.text
        assert response.json()["delta_fee"] == "0.00"

    negative = client.post(
        "/venues/me/timesheet/charges/charge-waived/correct",
        json={"delta_hours": "-7.00", "reason": "Testing the floor"},
        headers=OPERATOR,
    )
    assert negative.status_code == 400
    assert "below zero" in negative.text

    zero = client.post(
        "/venues/me/timesheet/charges/charge-waived/correct",
        json={"delta_hours": "0", "reason": "Testing the floor"},
        headers=OPERATOR,
    )
    assert zero.status_code == 400

    missing = client.post(
        "/venues/me/timesheet/charges/charge-unknown/correct",
        json={"delta_hours": "1.00", "reason": "Testing the floor"},
        headers=OPERATOR,
    )
    assert missing.status_code == 404


def test_corrections_replay_under_the_same_idempotency_key(client, in_memory_repos):
    from apps.api.src.config import use_in_memory_repositories

    if not use_in_memory_repositories():
        from apps.api.src.db.database import SessionLocal
        from apps.api.src.db.models import UserModel

        with SessionLocal() as session, session.begin():
            session.add(
                UserModel(
                    user_id="operator-1",
                    email="correct-idem@example.com",
                    hashed_password="x",
                    role="operator",
                    is_active=True,
                    created_at=NOW,
                    updated_at=NOW,
                    email_verified=True,
                )
            )
    shift = _shift(in_memory_repos, "shift-1")
    booking = _booking(in_memory_repos, "bk-1", shift, "temp-1", BookingState.APPROVED, clocked=True)
    _seed_charge(booking, "charge-1")
    headers = {**OPERATOR, "Idempotency-Key": "correct-1"}
    body = {"delta_hours": "1.00", "reason": "Stayed for close-down", "now": AFTER.isoformat()}

    first = client.post("/venues/me/timesheet/charges/charge-1/correct", json=body, headers=headers)
    replay = client.post("/venues/me/timesheet/charges/charge-1/correct", json=body, headers=headers)
    assert replay.json()["adjustment_id"] == first.json()["adjustment_id"]
    assert len(shared_booking_charge_adjustment_repository().list_for_charge("charge-1")) == 1


def test_the_week_view_aggregates_scheduled_worked_and_approved_hours(client, in_memory_repos):
    approved_shift = _shift(in_memory_repos, "shift-approved")
    approved = _booking(
        in_memory_repos, "bk-approved", approved_shift, "staff-1", BookingState.APPROVED, "employed", clocked=True
    )
    _seed_charge(approved, "charge-1", fee_percent="0.00", fee="0.00")
    planned_shift = _shift(in_memory_repos, "shift-planned", start=START + timedelta(days=1), hours=4)
    _booking(in_memory_repos, "bk-planned", planned_shift, "staff-1", BookingState.CONFIRMED, "employed")
    clocked_shift = _shift(in_memory_repos, "shift-clocked", start=START + timedelta(days=2), role="Server")
    _booking(in_memory_repos, "bk-clocked", clocked_shift, "temp-1", BookingState.CHECKED_OUT, clocked=True)

    response = client.get(
        "/venues/me/timesheet", params={"week_start": WEEK_START.isoformat()}, headers=OPERATOR
    )
    assert response.status_code == 200, response.text
    body = response.json()

    staff, temp = body["workers"]
    assert (staff["worker_id"], staff["relationship_type"]) == ("staff-1", "permanent")
    assert staff["contracted_hours_per_week"] == "20.00"
    assert (staff["scheduled_hours"], staff["worked_hours"], staff["approved_hours"]) == ("9.00", "5.00", "5.00")
    assert [d["hours_source"] for d in staff["days"]] == ["approved", "scheduled"]
    assert staff["days"][0]["day"] == "2030-06-10"

    assert (temp["worker_id"], temp["relationship_type"]) == ("temp-1", "one_off")
    assert temp["contracted_hours_per_week"] is None
    assert [d["hours_source"] for d in temp["days"]] == ["clocked"]

    assert body["total_scheduled_hours"] == "14.00"
    assert body["total_worked_hours"] == "10.00"
    assert body["total_approved_hours"] == "5.00"
    assert body["total_approved_wages"] == "72.50"


def test_the_booking_response_says_whether_check_in_needs_a_code(client, in_memory_repos):
    shift = _shift(in_memory_repos, "shift-1")
    _booking(in_memory_repos, "bk-emp", shift, "staff-1", BookingState.CONFIRMED, "employed")
    other = _shift(in_memory_repos, "shift-2", start=START + timedelta(days=1))
    _booking(in_memory_repos, "bk-pin", other, "temp-1", BookingState.CONFIRMED, "pin")

    employed = client.get("/bookings/bk-emp", headers=STAFF).json()
    assert employed["check_in_requires_code"] is False
    pin = client.get("/bookings/bk-pin", headers=TEMP).json()
    assert pin["check_in_requires_code"] is True


def test_the_timesheet_is_scoped_to_the_operator_venue(client):
    other = {"X-Actor-Role": "operator", "X-Actor-Id": "operator-2", "X-Account-Id": "venue-2"}
    worker = client.get(
        "/venues/me/timesheet", params={"week_start": WEEK_START.isoformat()}, headers=STAFF
    )
    assert worker.status_code == 403
    unknown = client.post(
        "/venues/me/timesheet/bookings/bk-nope/adjust",
        json={
            "checked_in_at": START.isoformat(),
            "checked_out_at": END.isoformat(),
            "reason": "Not my booking",
        },
        headers=other,
    )
    assert unknown.status_code == 404

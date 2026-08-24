from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from apps.api.src import main
from apps.api.src.db.models import (
    AccountModel,
    OrganisationMembershipModel,
    OrganisationModel,
    ApplicationModel,
    BookingModel,
    ShiftModel,
    UserModel,
    WorkerProfileModel,
)
from packages.domain.src.booking_state import BookingState

pytestmark = pytest.mark.postgres

PASSWORD = "integration-pass-1"
INVITE_CODE = "pg-test-invite"
BASE_NOW = datetime(2030, 1, 1, 9, 0, 0, tzinfo=UTC)


@pytest.fixture()
def client(monkeypatch):
    monkeypatch.setenv("OPERATOR_INVITE_CODES", INVITE_CODE)
    monkeypatch.setattr("apps.api.src.routes.shifts.geocode", lambda location: (None, None))
    return TestClient(main.app)


def _db_session():
    from apps.api.src.db.database import SessionLocal

    return SessionLocal()


def _auth(token_response: dict) -> dict:
    return {"Authorization": f"Bearer {token_response['access_token']}"}


def _register_worker(client: TestClient, email: str) -> dict:
    response = client.post("/auth/register", json={"email": email, "password": PASSWORD})
    assert response.status_code == 200, response.text
    return response.json()


def _register_verified_operator(client: TestClient, email: str) -> dict:
    response = client.post(
        "/auth/register/operator",
        json={
            "email": email,
            "password": PASSWORD,
            "venue_name": "The Test Tavern",
            "country": "GB",
            "market_id": "bath-gb",
            "invite_code": INVITE_CODE,
        },
    )
    assert response.status_code == 200, response.text
    operator = response.json()

    with _db_session() as session:
        user = session.get(UserModel, operator["user_id"])
        token = user.email_verification_token
    verify = client.post("/auth/verify-email", json={"token": token})
    assert verify.status_code == 200, verify.text
    return operator


def _create_shift(client: TestClient, operator: dict, workers_needed: int = 1) -> dict:
    response = client.post(
        "/shifts",
        json={
            "role": "server",
            "location": "Bath",
            "start_time": (BASE_NOW + timedelta(hours=2)).isoformat(),
            "end_time": (BASE_NOW + timedelta(hours=6)).isoformat(),
            "pay_rate": 15.5,
            "workers_needed": workers_needed,
            "now": BASE_NOW.isoformat(),
        },
        headers=_auth(operator),
    )
    assert response.status_code == 200, response.text
    return response.json()


def test_created_shift_geocoding_is_committed(client, monkeypatch) -> None:
    monkeypatch.setattr("apps.api.src.routes.shifts.geocode", lambda location: (51.3811, -2.3590))
    operator = _register_verified_operator(client, "geo-operator@example.com")

    shift = _create_shift(client, operator)

    with _db_session() as session:
        stored = session.get(ShiftModel, shift["shift_id"])
        assert stored.latitude == pytest.approx(51.3811)
        assert stored.longitude == pytest.approx(-2.3590)


def _apply(client: TestClient, worker: dict, shift_id: str) -> dict:
    response = client.post(
        "/applications",
        json={
            "shift_id": shift_id,
            "worker_id": worker["worker_profile_id"],
            "message": "Ready to help.",
            "now": (BASE_NOW + timedelta(minutes=30)).isoformat(),
        },
        headers=_auth(worker),
    )
    assert response.status_code == 200, response.text
    return response.json()


def _approve(client: TestClient, operator: dict, application_id: str):
    return client.post(
        f"/applications/{application_id}/approve",
        json={"now": (BASE_NOW + timedelta(hours=1)).isoformat()},
        headers=_auth(operator),
    )


def _approved_booking(client: TestClient) -> tuple[dict, dict, dict, str]:
    operator = _register_verified_operator(client, "operator@pg-test.example")
    worker = _register_worker(client, "worker@pg-test.example")
    shift = _create_shift(client, operator)
    application = _apply(client, worker, shift["shift_id"])
    approval = _approve(client, operator, application["application_id"])
    assert approval.status_code == 200, approval.text
    booking_id = approval.json()["booking_id"]
    assert booking_id
    return operator, worker, shift, booking_id


def test_backend_is_actually_postgresql(client: TestClient):
    from apps.api.src.db.database import engine

    assert engine.dialect.name == "postgresql"

    worker = _register_worker(client, "backend-proof@pg-test.example")
    with engine.connect() as connection:
        stored = connection.execute(
            select(UserModel.user_id).where(UserModel.user_id == worker["user_id"])
        ).scalar_one_or_none()
    assert stored == worker["user_id"]


def test_registration_persists_user_account_and_profile(client: TestClient):
    worker = _register_worker(client, "reg-worker@pg-test.example")
    operator = _register_verified_operator(client, "reg-operator@pg-test.example")

    with _db_session() as session:
        worker_user = session.get(UserModel, worker["user_id"])
        assert worker_user.role == "worker"
        assert session.get(WorkerProfileModel, worker["worker_profile_id"]) is not None

        operator_user = session.get(UserModel, operator["user_id"])
        assert operator_user.role == "operator"
        assert operator_user.email_verified is True
        account = session.get(AccountModel, operator["account_id"])
        assert account.name == "The Test Tavern"
        assert account.currency == "GBP"
        organisation = session.get(OrganisationModel, operator["organisation_id"])
        membership = session.get(
            OrganisationMembershipModel,
            (organisation.organisation_id, operator["user_id"]),
        )
        assert account.organisation_id == organisation.organisation_id
        assert membership.role == "owner"


def test_approval_creates_booking_and_fills_shift(client: TestClient):
    operator, worker, shift, booking_id = _approved_booking(client)

    with _db_session() as session:
        booking = session.get(BookingModel, booking_id)
        assert booking.state == BookingState.CONFIRMED
        assert booking.worker_id == worker["worker_profile_id"]

        application = session.execute(
            select(ApplicationModel).where(ApplicationModel.shift_id == shift["shift_id"])
        ).scalar_one()
        assert application.status == "approved"
        assert application.booking_id == booking_id

        stored_shift = session.get(ShiftModel, shift["shift_id"])
        assert stored_shift.workers_filled == 1
        assert stored_shift.status == "filled"


def test_approving_second_application_on_full_shift_fails(client: TestClient):
    operator = _register_verified_operator(client, "operator@pg-test.example")
    first_worker = _register_worker(client, "worker@pg-test.example")
    second_worker = _register_worker(client, "second-worker@pg-test.example")
    shift = _create_shift(client, operator)
    first_application = _apply(client, first_worker, shift["shift_id"])
    second_application = _apply(client, second_worker, shift["shift_id"])

    first_approval = _approve(client, operator, first_application["application_id"])
    assert first_approval.status_code == 200, first_approval.text

    response = _approve(client, operator, second_application["application_id"])
    assert response.status_code == 400, response.text

    with _db_session() as session:
        stored_shift = session.get(ShiftModel, shift["shift_id"])
        assert stored_shift.workers_filled == 1
        bookings = session.execute(
            select(BookingModel).where(BookingModel.shift_id == shift["shift_id"])
        ).scalars().all()
        assert len(bookings) == 1


def test_worker_cancellation_reopens_shift(client: TestClient):
    _, worker, shift, booking_id = _approved_booking(client)

    response = client.post(
        f"/bookings/{booking_id}/cancel/worker",
        json={
            "reason": "I am no longer available.",
            "now": (BASE_NOW + timedelta(hours=1, minutes=30)).isoformat(),
        },
        headers=_auth(worker),
    )
    assert response.status_code == 200, response.text

    with _db_session() as session:
        booking = session.get(BookingModel, booking_id)
        assert booking.state == BookingState.CANCELLED_BY_WORKER
        stored_shift = session.get(ShiftModel, shift["shift_id"])
        assert stored_shift.workers_filled == 0
        assert stored_shift.status == "open"


def test_operator_no_show_reopens_shift_and_updates_reliability(client: TestClient):
    operator, worker, shift, booking_id = _approved_booking(client)

    response = client.post(
        f"/bookings/{booking_id}/no-show",
        json={"now": (BASE_NOW + timedelta(hours=7)).isoformat()},
        headers=_auth(operator),
    )
    assert response.status_code == 200, response.text

    with _db_session() as session:
        booking = session.get(BookingModel, booking_id)
        assert booking.state == BookingState.NO_SHOW
        stored_shift = session.get(ShiftModel, shift["shift_id"])
        assert stored_shift.workers_filled == 0
        assert stored_shift.status == "open"
        profile = session.get(WorkerProfileModel, worker["worker_profile_id"])
        assert profile.updated_at == BASE_NOW + timedelta(hours=7)

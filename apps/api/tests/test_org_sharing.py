from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient

from apps.api.src import main
from apps.api.src.db.models import BookingModel, UserModel
from apps.api.src.db.booking_charge_models import BookingChargeModel

pytestmark = pytest.mark.postgres

INVITE_CODE = "org-sharing-test-invite"
PASSWORD = "org-sharing-pass-1"


@pytest.fixture()
def client(monkeypatch):
    monkeypatch.setenv("OPERATOR_INVITE_CODES", INVITE_CODE)
    monkeypatch.setattr("apps.api.src.routes.shifts.geocode", lambda location: (None, None))
    return TestClient(main.app)


def _session():
    from apps.api.src.db.database import SessionLocal

    return SessionLocal()


def _headers(payload: dict) -> dict[str, str]:
    return {"Authorization": f"Bearer {payload['access_token']}"}


def _register_operator(client: TestClient, email: str, venue_name: str) -> dict:
    response = client.post(
        "/auth/register/operator",
        json={
            "email": email,
            "password": PASSWORD,
            "venue_name": venue_name,
            "country": "GB",
            "market_id": "bath-gb",
            "invite_code": INVITE_CODE,
        },
    )
    assert response.status_code == 200, response.text
    operator = response.json()
    with _session() as session:
        session.get(UserModel, operator["user_id"]).email_verified = True
        session.commit()
    return operator


def _register_worker(client: TestClient, email: str) -> tuple[dict, str]:
    response = client.post(
        "/auth/register", json={"email": email, "password": PASSWORD + "w"}
    )
    assert response.status_code == 200, response.text
    worker = response.json()
    with _session() as session:
        row = session.get(UserModel, worker["user_id"])
        row.email_verified = True
        session.commit()
        worker_id = row.worker_profile_id or row.user_id
    login = client.post("/auth/login", json={"email": email, "password": PASSWORD + "w"})
    return login.json(), worker_id


def _employ(client: TestClient, owner: dict, worker: dict, worker_id: str) -> None:
    invited = client.post(
        f"/venues/me/people/{worker_id}/invite",
        json={"relationship_type": "permanent"},
        headers=_headers(owner),
    )
    assert invited.status_code == 200, invited.text
    for invitation in client.get("/me/invitations", headers=_headers(worker)).json():
        accepted = client.post(
            f"/me/invitations/{invitation['relationship_id']}/accept",
            json={},
            headers=_headers(worker),
        )
        assert accepted.status_code == 200, accepted.text


def _switch(client: TestClient, owner: dict, venue_id: str) -> dict:
    switched = client.post(
        "/auth/switch-venue", json={"venue_id": venue_id}, headers=_headers(owner)
    )
    assert switched.status_code == 200, switched.text
    return switched.json()


def _monday_next_week() -> datetime:
    now = datetime.now(UTC)
    monday = now + timedelta(days=(7 - now.weekday()) % 7 or 7)
    return datetime(monday.year, monday.month, monday.day, 18, 0, tzinfo=UTC) + timedelta(days=7)


def test_a_sibling_employee_is_offered_not_booked_and_zero_rated(client: TestClient):
    owner = _register_operator(client, "owner@sharing.example", "The Ship")
    second = client.post(
        "/organisations/me/venues",
        json={"name": "The Ship Deckhouse", "market_id": "bath-gb"},
        headers=_headers(owner),
    ).json()
    worker, worker_id = _register_worker(client, "crew@sharing.example")
    _employ(client, owner, worker, worker_id)

    at_second = _switch(client, owner, second["venue_id"])
    start = _monday_next_week()
    end = start + timedelta(hours=4)
    draft = client.post(
        "/shifts",
        json={
            "role": "Server",
            "location": "Deckhouse",
            "start_time": start.isoformat(),
            "end_time": end.isoformat(),
            "pay_rate": 15.0,
            "workers_needed": 1,
            "assigned_worker_id": worker_id,
            "rota_state": "draft",
        },
        headers=_headers(at_second),
    )
    assert draft.status_code == 200, draft.text
    week_start = start.date() - timedelta(days=start.weekday())
    published = client.post(
        "/venues/me/rota/publish",
        json={"week_start": week_start.isoformat()},
        headers=_headers(at_second),
    )
    assert published.status_code == 200, published.text
    body = published.json()
    assert body["booked_worker_ids"] == []
    assert worker_id in body["offered_worker_ids"]

    offers = [
        offer
        for offer in client.get("/me/shift-offers", headers=_headers(worker)).json()
        if offer["status"] == "pending" and offer["shift_id"] == draft.json()["shift_id"]
    ]
    assert len(offers) == 1
    accepted = client.post(
        f"/me/shift-offers/{offers[0]['offer_id']}/accept",
        json={},
        headers=_headers(worker),
    )
    assert accepted.status_code == 200, accepted.text

    with _session() as session:
        booking = (
            session.query(BookingModel)
            .filter(BookingModel.shift_id == draft.json()["shift_id"])
            .one()
        )
        assert booking.attendance_mode == "pin"
        assert booking.allocation_source == "assigned"
        booking_id = booking.booking_id

    code = client.get(f"/bookings/{booking_id}", headers=_headers(at_second)).json()[
        "check_in_code"
    ]
    checked_in = client.post(
        f"/bookings/{booking_id}/check-in",
        json={"code": code, "now": start.isoformat()},
        headers=_headers(worker),
    )
    assert checked_in.status_code == 200, checked_in.text
    completion = client.get(f"/bookings/{booking_id}", headers=_headers(worker)).json()[
        "completion_code"
    ]
    client.post(
        f"/bookings/{booking_id}/check-out",
        json={"now": end.isoformat()},
        headers=_headers(worker),
    )
    approved = client.post(
        f"/bookings/{booking_id}/approve",
        json={"code": completion, "now": end.isoformat()},
        headers=_headers(at_second),
    )
    assert approved.status_code == 200, approved.text

    with _session() as session:
        charge = (
            session.query(BookingChargeModel)
            .filter(BookingChargeModel.booking_id == booking_id)
            .one()
        )
        assert charge.fee == 0
        assert charge.fee_basis == "organisation_employed"
        assert charge.source_venue_id == owner["venue_id"]

    rollup = client.get(
        f"/organisations/me/billing/summary?month={end.strftime('%Y-%m')}",
        headers=_headers(owner),
    )
    assert rollup.status_code == 200, rollup.text
    body = rollup.json()
    assert {row["venue_id"] for row in body["venues"]} == {
        owner["venue_id"],
        second["venue_id"],
    }
    assert body["amount_due"] == body["fee_total"]


def test_org_staff_listing_shows_people_across_venues(client: TestClient):
    owner = _register_operator(client, "owner2@sharing.example", "The Wharf")
    client.post(
        "/organisations/me/venues",
        json={"name": "The Wharf Loft", "market_id": "bath-gb"},
        headers=_headers(owner),
    )
    worker, worker_id = _register_worker(client, "crew2@sharing.example")
    _employ(client, owner, worker, worker_id)

    staff = client.get("/organisations/me/staff", headers=_headers(owner))
    assert staff.status_code == 200, staff.text
    rows = staff.json()
    assert any(
        row["person"]["worker_id"] == worker_id and row["venue_id"] == owner["venue_id"]
        for row in rows
    )


def test_a_venue_with_no_relationships_still_posts_and_fills(client: TestClient):
    owner = _register_operator(client, "owner3@sharing.example", "The Loner")
    worker, worker_id = _register_worker(client, "crew3@sharing.example")
    with _session() as session:
        from apps.api.src.db.models import WorkerProfileModel

        profile = session.get(WorkerProfileModel, worker_id)
        profile.market_id = "bath-gb"
        profile.city = "Bath"
        session.commit()

    start = _monday_next_week() + timedelta(days=1)
    shift = client.post(
        "/shifts",
        json={
            "role": "Host",
            "location": "Front door",
            "start_time": start.isoformat(),
            "end_time": (start + timedelta(hours=4)).isoformat(),
            "pay_rate": 13.0,
            "workers_needed": 1,
        },
        headers=_headers(owner),
    )
    assert shift.status_code == 200, shift.text
    application = client.post(
        "/applications",
        json={"shift_id": shift.json()["shift_id"], "worker_id": worker_id},
        headers=_headers(worker),
    )
    assert application.status_code == 200, application.text
    approved = client.post(
        f"/applications/{application.json()['application_id']}/approve",
        json={},
        headers=_headers(owner),
    )
    assert approved.status_code == 200, approved.text

    with _session() as session:
        booking = (
            session.query(BookingModel)
            .filter(BookingModel.shift_id == shift.json()["shift_id"])
            .one()
        )
        assert booking.allocation_source == "market"

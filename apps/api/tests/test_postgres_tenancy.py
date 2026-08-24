from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient

from apps.api.src import main
from apps.api.src.db.models import (
    OrganisationMembershipModel,
    OrganisationModel,
    UserModel,
    VenueModel,
)

pytestmark = pytest.mark.postgres

INVITE_CODE = "tenancy-test-invite"
PASSWORD = "tenancy-pass-1"
BASE_NOW = datetime(2030, 2, 1, 12, 0, tzinfo=UTC)


@pytest.fixture()
def client(monkeypatch):
    monkeypatch.setenv("OPERATOR_INVITE_CODES", INVITE_CODE)
    monkeypatch.setattr("apps.api.src.routes.shifts.geocode", lambda location: (None, None))
    return TestClient(main.app)


def _session():
    from apps.api.src.db.database import SessionLocal

    return SessionLocal()


def _headers(operator: dict) -> dict[str, str]:
    return {"Authorization": f"Bearer {operator['access_token']}"}


def _register(client: TestClient, email: str, venue_name: str) -> dict:
    response = client.post(
        "/auth/register/operator",
        json={
            "email": email,
            "password": PASSWORD,
            "organisation_name": f"{venue_name} Group",
            "venue_name": venue_name,
            "country": "GB",
            "market_id": "bath-gb",
            "invite_code": INVITE_CODE,
        },
    )
    assert response.status_code == 200, response.text
    return response.json()


def _verify(operator: dict) -> None:
    with _session() as session:
        user = session.get(UserModel, operator["user_id"])
        user.email_verified = True
        session.commit()


def test_registration_creates_one_organisation_venue_and_owner_membership(client: TestClient):
    operator = _register(client, "owner@tenancy.example", "Bath Brewhouse")

    assert operator["account_id"] == operator["venue_id"]
    assert operator["organisation_id"] != operator["venue_id"]
    with _session() as session:
        organisation = session.get(OrganisationModel, operator["organisation_id"])
        venue = session.get(VenueModel, operator["venue_id"])
        membership = session.get(
            OrganisationMembershipModel,
            (operator["organisation_id"], operator["user_id"]),
        )
        user = session.get(UserModel, operator["user_id"])
        assert organisation.name == "Bath Brewhouse Group"
        assert venue.name == "Bath Brewhouse"
        assert venue.organisation_id == organisation.organisation_id
        assert membership.role == "owner"
        assert user.active_venue_id == venue.venue_id


def test_operator_can_read_organisation_and_all_its_venues(client: TestClient):
    operator = _register(client, "manager@tenancy.example", "Bath Brewhouse")
    with _session() as session:
        session.add(
            VenueModel(
                venue_id="ciderhouse-venue",
                organisation_id=operator["organisation_id"],
                name="Bath Cider House",
                country="GB",
                currency="GBP",
                created_at=BASE_NOW,
            )
        )
        session.commit()

    organisation = client.get("/organisations/me", headers=_headers(operator))
    venues = client.get("/venues", headers=_headers(operator))
    legacy_venue = client.get("/accounts/me", headers=_headers(operator))
    canonical_venue = client.get("/venues/me", headers=_headers(operator))

    assert organisation.status_code == 200, organisation.text
    assert organisation.json()["membership_role"] == "owner"
    assert {venue["name"] for venue in venues.json()} == {"Bath Brewhouse", "Bath Cider House"}
    assert canonical_venue.json() == legacy_venue.json()


def test_separate_registrations_are_isolated_organisations_and_venues(client: TestClient):
    first = _register(client, "first@tenancy.example", "First Venue")
    second = _register(client, "second@tenancy.example", "Second Venue")
    _verify(first)

    create = client.post(
        "/shifts",
        json={
            "role": "bartender",
            "location": "Bath",
            "start_time": (BASE_NOW + timedelta(hours=1)).isoformat(),
            "end_time": (BASE_NOW + timedelta(hours=5)).isoformat(),
            "pay_rate": "14.50",
            "workers_needed": 1,
            "now": BASE_NOW.isoformat(),
        },
        headers=_headers(first),
    )
    assert create.status_code == 200, create.text
    shift_id = create.json()["shift_id"]

    assert first["organisation_id"] != second["organisation_id"]
    assert first["venue_id"] != second["venue_id"]
    second_list = client.get("/shifts", headers=_headers(second))
    second_read = client.get(f"/shifts/{shift_id}", headers=_headers(second))
    assert second_list.json() == []
    assert second_read.status_code == 403


def test_operator_scope_requires_membership(client: TestClient):
    operator = _register(client, "removed@tenancy.example", "Former Venue")
    with _session() as session:
        membership = session.get(
            OrganisationMembershipModel,
            (operator["organisation_id"], operator["user_id"]),
        )
        session.delete(membership)
        session.commit()

    response = client.get("/auth/me", headers=_headers(operator))
    assert response.status_code == 403
    assert response.json()["detail"] == "Operator is not a member of this organisation."

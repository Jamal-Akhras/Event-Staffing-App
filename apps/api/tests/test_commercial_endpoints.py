from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient

from apps.api.src import main
from apps.api.src.db.models import UserModel

pytestmark = pytest.mark.postgres

INVITE_CODE = "commercial-test-invite"
PASSWORD = "commercial-pass-1"


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


def _register(client: TestClient, email: str, venue_name: str) -> dict:
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


def test_plan_change_and_boost_appear_on_the_statement(client: TestClient):
    owner = _register(client, "owner@commercial.example", "The Crown")

    plan = client.get("/organisations/me/plan", headers=_headers(owner))
    assert plan.status_code == 200, plan.text
    assert plan.json()["plan"] == "classic"

    changed = client.put(
        "/organisations/me/plan", json={"plan": "plus"}, headers=_headers(owner)
    )
    assert changed.status_code == 200, changed.text
    assert changed.json()["plan"] == "plus"
    assert changed.json()["own_pool_fee_percent"] == "0.00"

    start = datetime.now(UTC) + timedelta(days=5)
    shift = client.post(
        "/shifts",
        json={
            "role": "Bartender",
            "location": "Main bar",
            "start_time": start.isoformat(),
            "end_time": (start + timedelta(hours=5)).isoformat(),
            "pay_rate": 14.0,
            "workers_needed": 1,
        },
        headers=_headers(owner),
    )
    assert shift.status_code == 200, shift.text
    boost = client.post(
        f"/shifts/{shift.json()['shift_id']}/boost",
        json={"tier": "top5"},
        headers=_headers(owner),
    )
    assert boost.status_code == 201, boost.text
    assert boost.json()["price"] == "8.00"

    duplicate = client.post(
        f"/shifts/{shift.json()['shift_id']}/boost",
        json={"tier": "top1"},
        headers=_headers(owner),
    )
    assert duplicate.status_code == 409

    period = datetime.now(UTC).strftime("%Y-%m")
    from apps.api.src.jobs.run_subscription_minting import run

    minted = run(period=period)
    assert minted >= 1

    summary = client.get(
        f"/billing/summary?month={period}", headers=_headers(owner)
    )
    assert summary.status_code == 200, summary.text
    body = summary.json()
    assert body["plan"] == "plus"
    assert body["boost_total"] == "8.00"
    assert body["subscription_total"] == "25.00"
    assert [line["tier"] for line in body["boost_lines"]] == ["top5"]
    assert body["subscription_lines"][0]["amount"] == "25.00"
    assert body["amount_due"] == "33.00"


def test_a_manager_cannot_change_the_plan_or_boost(client: TestClient):
    owner = _register(client, "owner2@commercial.example", "The Mitre")
    second = client.post(
        "/organisations/me/venues",
        json={"name": "The Mitre Vaults", "market_id": "bath-gb"},
        headers=_headers(owner),
    ).json()
    invitation = client.post(
        "/organisations/me/members/invite",
        json={"email": "manager@commercial.example", "role": "manager", "venue_ids": [second["venue_id"]]},
        headers=_headers(owner),
    ).json()
    manager = client.post(
        "/auth/register/invited",
        json={"email": "manager@commercial.example", "password": PASSWORD, "token": invitation["token"]},
    ).json()

    blocked = client.put(
        "/organisations/me/plan", json={"plan": "plus"}, headers=_headers(manager)
    )
    assert blocked.status_code == 403

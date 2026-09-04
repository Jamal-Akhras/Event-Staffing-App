from __future__ import annotations

from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient

from apps.api.src import main
from apps.api.src.db.models import UserModel
from apps.api.src.db.notification_models import NotificationModel

pytestmark = pytest.mark.postgres

INVITE_CODE = "org-admin-test-invite"
PASSWORD = "org-admin-pass-1"


@pytest.fixture()
def client(monkeypatch):
    monkeypatch.setenv("OPERATOR_INVITE_CODES", INVITE_CODE)
    return TestClient(main.app)


def _session():
    from apps.api.src.db.database import SessionLocal

    return SessionLocal()


def _headers(token_payload: dict) -> dict[str, str]:
    return {"Authorization": f"Bearer {token_payload['access_token']}"}


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
        user = session.get(UserModel, operator["user_id"])
        user.email_verified = True
        session.commit()
    return operator


def _create_venue(client: TestClient, owner: dict, name: str) -> dict:
    response = client.post(
        "/organisations/me/venues",
        json={"name": name, "market_id": "bath-gb"},
        headers=_headers(owner),
    )
    assert response.status_code == 200, response.text
    return response.json()


def _invite(client: TestClient, owner: dict, email: str, role: str, venue_ids=None) -> dict:
    response = client.post(
        "/organisations/me/members/invite",
        json={"email": email, "role": role, "venue_ids": venue_ids},
        headers=_headers(owner),
    )
    assert response.status_code == 200, response.text
    return response.json()


def _join(client: TestClient, email: str, token: str) -> dict:
    response = client.post(
        "/auth/register/invited",
        json={"email": email, "password": PASSWORD, "token": token},
    )
    assert response.status_code == 200, response.text
    return response.json()


def test_invitation_lifecycle_creates_a_scoped_manager(client: TestClient):
    owner = _register(client, "owner@orgadmin.example", "The Raven")
    second = _create_venue(client, owner, "The Raven Cellars")
    invitation = _invite(
        client, owner, "manager@orgadmin.example", "manager", [second["venue_id"]]
    )

    manager = _join(client, "manager@orgadmin.example", invitation["token"])
    assert manager["venue_id"] == second["venue_id"]

    members = client.get("/organisations/me/members", headers=_headers(owner)).json()
    by_email = {member["email"]: member for member in members}
    assert by_email["manager@orgadmin.example"]["role"] == "manager"
    assert by_email["manager@orgadmin.example"]["venue_ids"] == [second["venue_id"]]

    reused = client.post(
        "/auth/register/invited",
        json={"email": "other@orgadmin.example", "password": PASSWORD, "token": invitation["token"]},
    )
    assert reused.status_code == 400


def test_the_role_matrix_holds_at_sensitive_routes(client: TestClient):
    owner = _register(client, "owner2@orgadmin.example", "The Griffin")
    second = _create_venue(client, owner, "The Griffin Yard")
    invitation = _invite(
        client, owner, "manager2@orgadmin.example", "manager", [second["venue_id"]]
    )
    manager = _join(client, "manager2@orgadmin.example", invitation["token"])

    assert client.get("/billing/summary", headers=_headers(manager)).status_code == 403
    assert (
        client.put(
            "/accounts/me", json={"name": "Renamed"}, headers=_headers(manager)
        ).status_code
        == 403
    )
    assert (
        client.post(
            "/organisations/me/venues",
            json={"name": "Rogue", "market_id": "bath-gb"},
            headers=_headers(manager),
        ).status_code
        == 403
    )
    assert client.get("/organisations/me/members", headers=_headers(manager)).status_code == 403
    assert client.get("/billing/summary", headers=_headers(owner)).status_code == 200


def test_a_scoped_manager_cannot_enter_an_uncovered_venue(client: TestClient):
    owner = _register(client, "owner3@orgadmin.example", "The Lantern")
    second = _create_venue(client, owner, "The Lantern Annex")
    invitation = _invite(
        client, owner, "manager3@orgadmin.example", "manager", [second["venue_id"]]
    )
    manager = _join(client, "manager3@orgadmin.example", invitation["token"])

    blocked = client.post(
        "/auth/switch-venue",
        json={"venue_id": owner["venue_id"]},
        headers=_headers(manager),
    )
    assert blocked.status_code == 400

    allowed = client.get("/accounts/me", headers=_headers(manager))
    assert allowed.status_code == 200
    assert allowed.json()["account_id"] == second["venue_id"]


def test_switching_venue_scopes_only_the_new_session(client: TestClient):
    owner = _register(client, "owner4@orgadmin.example", "The Beacon")
    second = _create_venue(client, owner, "The Beacon Rooftop")

    switched = client.post(
        "/auth/switch-venue", json={"venue_id": second["venue_id"]}, headers=_headers(owner)
    )
    assert switched.status_code == 200, switched.text
    new_session = switched.json()

    fresh = client.get("/accounts/me", headers=_headers(new_session)).json()
    assert fresh["account_id"] == second["venue_id"]
    stale = client.get("/accounts/me", headers=_headers(owner)).json()
    assert stale["account_id"] == owner["venue_id"]


def test_the_last_owner_cannot_be_demoted_or_removed(client: TestClient):
    owner = _register(client, "owner5@orgadmin.example", "The Anchor")

    demoted = client.put(
        f"/organisations/me/members/{owner['user_id']}",
        json={"role": "admin"},
        headers=_headers(owner),
    )
    assert demoted.status_code == 400

    invitation = _invite(client, owner, "admin5@orgadmin.example", "admin")
    admin = _join(client, "admin5@orgadmin.example", invitation["token"])
    removed = client.delete(
        f"/organisations/me/members/{admin['user_id']}", headers=_headers(owner)
    )
    assert removed.status_code == 204
    members = client.get("/organisations/me/members", headers=_headers(owner)).json()
    assert [member["user_id"] for member in members] == [owner["user_id"]]


def test_venue_notifications_track_read_state_per_member(client: TestClient):
    owner = _register(client, "owner6@orgadmin.example", "The Foundry")
    invitation = _invite(client, owner, "admin6@orgadmin.example", "admin")
    admin = _join(client, "admin6@orgadmin.example", invitation["token"])

    with _session() as session:
        session.add(
            NotificationModel(
                notification_id="orgadmin-notif-1",
                venue_id=owner["venue_id"],
                type="test.event",
                title="A slot needs attention",
                body="Someone dropped a shift.",
                read=False,
                created_at=datetime(2030, 3, 1, 12, 0, tzinfo=UTC),
            )
        )
        session.commit()

    marked = client.post("/notifications/read-all", headers=_headers(owner))
    assert marked.status_code == 200
    assert marked.json()["marked_read"] == 1

    owner_page = client.get("/notifications", headers=_headers(owner)).json()
    assert owner_page["unread_count"] == 0

    admin_page = client.get("/notifications", headers=_headers(admin)).json()
    admin_items = {
        item["notification_id"]: item for item in admin_page["items"]
    }
    assert admin_items["orgadmin-notif-1"]["read"] is False
    assert admin_page["unread_count"] >= 1

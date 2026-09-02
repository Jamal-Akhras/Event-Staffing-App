from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient

from apps.api.src import main
from apps.api.src.models.account import Account
from apps.api.src.models.worker_profile import WorkerProfile
from apps.api.src.repository_dependencies import get_account_repo, get_worker_profile_repo
from apps.api.src.repository_dependencies_workforce import (
    shared_relationship_transition_repository,
    shared_venue_join_code_repository,
    shared_worker_relationship_repository,
)

VENUE_ID = "venue-1"
WORKER_ID = "worker-1"
NOW = datetime.now(UTC)
OPERATOR = {"X-Actor-Role": "operator", "X-Actor-Id": "operator-1", "X-Account-Id": VENUE_ID}
OTHER_OPERATOR = {"X-Actor-Role": "operator", "X-Actor-Id": "operator-2", "X-Account-Id": "venue-2"}
WORKER = {"X-Actor-Role": "worker", "X-Actor-Id": WORKER_ID}


@pytest.fixture(autouse=True)
def clear_state():
    for repo in (
        shared_venue_join_code_repository(),
        shared_worker_relationship_repository(),
        shared_relationship_transition_repository(),
    ):
        repo.clear()
    yield
    for repo in (
        shared_venue_join_code_repository(),
        shared_worker_relationship_repository(),
        shared_relationship_transition_repository(),
    ):
        repo.clear()


@pytest.fixture()
def client(in_memory_repos):
    accounts = in_memory_repos[get_account_repo]
    accounts.save(Account(account_id=VENUE_ID, name="The Grapes", country="GB", currency="GBP", created_at=NOW))
    accounts.save(Account(account_id="venue-2", name="Other Bar", country="GB", currency="GBP", created_at=NOW))
    in_memory_repos[get_worker_profile_repo].save(
        WorkerProfile(
            worker_id=WORKER_ID,
            display_name="Alex Worker",
            role="Bartender",
            city="Bath",
            experience_years=2,
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
            updated_at=NOW,
        )
    )
    return TestClient(main.app)


def _create(client: TestClient, **overrides) -> dict:
    payload = {"relationship_type": "permanent", "max_redemptions": 2, "default_role": "Bartender"}
    payload.update(overrides)
    response = client.post("/venues/me/join-codes", json=payload, headers=OPERATOR)
    assert response.status_code == 201, response.text
    return response.json()


def test_a_join_code_cannot_create_pool_membership(client):
    for blocked in ("pool", "one_off"):
        response = client.post(
            "/venues/me/join-codes",
            json={"relationship_type": blocked, "max_redemptions": 1},
            headers=OPERATOR,
        )
        assert response.status_code == 422, response.text


def test_redeeming_creates_one_relationship_and_one_transition(client):
    code = _create(client)["code"]
    response = client.post(f"/join-codes/{code}/redeem", headers=WORKER)
    assert response.status_code == 200, response.text
    body = response.json()
    assert (body["relationship_type"], body["status"]) == ("permanent", "active")
    assert body["default_role"] == "Bartender"

    relationships = shared_worker_relationship_repository().list_for_venue(VENUE_ID)
    assert len(relationships) == 1
    transitions = shared_relationship_transition_repository().list_for_relationship(body["relationship_id"])
    assert len(transitions) == 1
    assert transitions[0].from_relationship_type is None


def test_redeeming_twice_adds_nothing(client):
    code = _create(client)["code"]
    first = client.post(f"/join-codes/{code}/redeem", headers=WORKER).json()
    second = client.post(f"/join-codes/{code}/redeem", headers=WORKER).json()

    assert first["relationship_id"] == second["relationship_id"]
    assert len(shared_worker_relationship_repository().list_for_venue(VENUE_ID)) == 1
    assert shared_venue_join_code_repository().count_redemptions(code) == 1


def test_redeeming_past_the_limit_is_refused(client):
    code = _create(client, max_redemptions=1)["code"]
    assert client.post(f"/join-codes/{code}/redeem", headers=WORKER).status_code == 200

    other = {"X-Actor-Role": "worker", "X-Actor-Id": "worker-2"}
    response = client.post(f"/join-codes/{code}/redeem", headers=other)
    assert response.status_code == 400
    assert "maximum number of times" in response.text


def test_a_revoked_code_is_refused(client):
    code = _create(client)["code"]
    revoked = client.delete(f"/venues/me/join-codes/{code}", headers=OPERATOR)
    assert revoked.status_code == 200, revoked.text
    assert revoked.json()["revoked_at"] is not None

    response = client.post(f"/join-codes/{code}/redeem", headers=WORKER)
    assert response.status_code == 400
    assert "turned off" in response.text


def test_an_expired_code_is_refused(client):
    from dataclasses import replace

    code = _create(client, expires_at=(NOW + timedelta(days=30)).isoformat())["code"]
    codes = shared_venue_join_code_repository()
    codes.save_code(replace(codes.get_code(code), expires_at=NOW - timedelta(days=1)))

    response = client.post(f"/join-codes/{code}/redeem", headers=WORKER)
    assert response.status_code == 400
    assert "expired" in response.text


def test_preview_gives_the_venue_name_and_nothing_more(client):
    code = _create(client)["code"]
    body = client.get(f"/join-codes/{code}").json()
    assert body == {
        "code": code,
        "venue_name": "The Grapes",
        "relationship_type": "permanent",
        "default_role": "Bartender",
    }


def test_a_venue_cannot_revoke_another_venues_code(client):
    code = _create(client)["code"]
    response = client.delete(f"/venues/me/join-codes/{code}", headers=OTHER_OPERATOR)
    assert response.status_code == 404


def test_listing_shows_how_many_times_a_code_has_been_used(client):
    code = _create(client)["code"]
    client.post(f"/join-codes/{code}/redeem", headers=WORKER)
    listed = client.get("/venues/me/join-codes", headers=OPERATOR).json()
    assert [(item["code"], item["redeemed"], item["max_redemptions"]) for item in listed] == [(code, 1, 2)]


def test_registering_with_a_code_joins_the_venue_team(client):
    code = _create(client)["code"]
    response = client.post(
        "/auth/register",
        json={"email": "new.starter@example.com", "password": "Temp1234!", "join_code": code},
    )
    assert response.status_code == 200, response.text
    worker_profile_id = response.json()["worker_profile_id"]

    relationships = shared_worker_relationship_repository().list_for_venue(VENUE_ID)
    assert [(item.worker_id, item.relationship_type) for item in relationships] == [
        (worker_profile_id, "permanent")
    ]


def test_registering_without_a_code_joins_nobodys_team(client):
    response = client.post(
        "/auth/register",
        json={"email": "open.pool@example.com", "password": "Temp1234!"},
    )
    assert response.status_code == 200, response.text
    assert shared_worker_relationship_repository().list_for_venue(VENUE_ID) == []


def test_registering_with_a_bad_code_creates_no_account(client):
    from apps.api.src.repository_dependencies import get_user_repo

    response = client.post(
        "/auth/register",
        json={"email": "typo@example.com", "password": "Temp1234!", "join_code": "TEAM-NOPE-NOPE"},
    )
    assert response.status_code == 404, response.text
    assert main.app.dependency_overrides[get_user_repo]().get_by_email("typo@example.com") is None

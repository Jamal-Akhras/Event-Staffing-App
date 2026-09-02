from dataclasses import replace
from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient

from apps.api.src import main
from apps.api.src.models.worker_profile import WorkerProfile
from apps.api.src.repository_dependencies import get_worker_profile_repo
from apps.api.src.repository_dependencies_workforce import (
    shared_relationship_transition_repository,
    shared_worker_relationship_repository,
)

VENUE_ID = "venue-1"
WORKER_ID = "worker-1"
NOW = datetime.now(UTC)
OPERATOR = {"X-Actor-Role": "operator", "X-Actor-Id": "operator-1", "X-Account-Id": VENUE_ID}
OTHER_OPERATOR = {"X-Actor-Role": "operator", "X-Actor-Id": "operator-2", "X-Account-Id": "venue-2"}


@pytest.fixture(autouse=True)
def clear_state():
    for repo in (shared_worker_relationship_repository(), shared_relationship_transition_repository()):
        repo.clear()
    yield
    for repo in (shared_worker_relationship_repository(), shared_relationship_transition_repository()):
        repo.clear()


@pytest.fixture()
def workers(in_memory_repos):
    repo = in_memory_repos[get_worker_profile_repo]
    repo.save(
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
            allow_venue_recontact=True,
        )
    )
    return repo


@pytest.fixture()
def client(workers):
    return TestClient(main.app)


def _worked_here(relationship_type: str = "one_off") -> None:
    from apps.api.src.models.worker_relationship import WorkerRelationship

    shared_worker_relationship_repository().save(
        WorkerRelationship(
            relationship_id="rel-1",
            venue_id=VENUE_ID,
            worker_id=WORKER_ID,
            relationship_type=relationship_type,
            status="active",
            created_at=NOW,
            updated_at=NOW,
        )
    )


def test_a_worker_who_has_worked_here_can_be_added_to_the_pool(client):
    _worked_here()
    response = client.post(f"/venues/me/people/{WORKER_ID}/pool", headers=OPERATOR)
    assert response.status_code == 200, response.text
    assert response.json()["relationship_type"] == "pool"

    transitions = shared_relationship_transition_repository().list_for_relationship("rel-1")
    assert [(item.from_relationship_type, item.to_relationship_type) for item in transitions] == [
        ("one_off", "pool")
    ]


def test_a_worker_who_has_never_worked_here_cannot_be_added(client):
    response = client.post(f"/venues/me/people/{WORKER_ID}/pool", headers=OPERATOR)
    assert response.status_code == 404
    assert "not worked at your venue" in response.text


def test_a_worker_who_turned_off_recontact_cannot_be_added(client, workers):
    _worked_here()
    workers.save(replace(workers.get(WORKER_ID), allow_venue_recontact=False))

    response = client.post(f"/venues/me/people/{WORKER_ID}/pool", headers=OPERATOR)
    assert response.status_code == 400
    assert "turned off contact" in response.text


def test_an_employed_worker_is_not_moved_into_the_pool(client):
    _worked_here("permanent")
    response = client.post(f"/venues/me/people/{WORKER_ID}/pool", headers=OPERATOR)
    assert response.status_code == 400
    assert "already employed" in response.text


def test_removing_from_the_pool_leaves_them_as_a_past_worker(client):
    _worked_here("pool")
    response = client.delete(f"/venues/me/people/{WORKER_ID}/pool", headers=OPERATOR)
    assert response.status_code == 200, response.text
    assert response.json()["relationship_type"] == "one_off"
    assert response.json()["status"] == "active"


def test_a_venue_only_sees_and_changes_its_own_people(client):
    _worked_here()
    assert client.post(f"/venues/me/people/{WORKER_ID}/pool", headers=OTHER_OPERATOR).status_code == 404
    assert client.get("/venues/me/people", headers=OTHER_OPERATOR).json() == []
    assert len(client.get("/venues/me/people", headers=OPERATOR).json()) == 1


WORKER_HEADERS = {"X-Actor-Role": "worker", "X-Actor-Id": WORKER_ID}


def test_a_venue_cannot_make_someone_employed_on_its_own(client):
    _worked_here()
    response = client.post(
        "/venues/me/people/worker-1/invite",
        json={"relationship_type": "permanent"},
        headers=OPERATOR,
    )
    assert response.status_code == 200, response.text
    assert response.json()["status"] == "invited"

    listed = client.get("/venues/me/people", headers=OPERATOR).json()
    assert listed[0]["status"] == "invited"
    assert listed[0]["relationship_type"] == "one_off"


def test_employment_only_becomes_real_when_the_worker_accepts(client):
    _worked_here()
    invited = client.post(
        "/venues/me/people/worker-1/invite",
        json={"relationship_type": "permanent"},
        headers=OPERATOR,
    ).json()

    pending = client.get("/me/invitations", headers=WORKER_HEADERS).json()
    assert [item["relationship_id"] for item in pending] == [invited["relationship_id"]]

    accepted = client.post(
        f"/me/invitations/{invited['relationship_id']}/accept", headers=WORKER_HEADERS
    )
    assert accepted.status_code == 200, accepted.text
    assert (accepted.json()["relationship_type"], accepted.json()["status"]) == ("permanent", "active")
    assert client.get("/me/invitations", headers=WORKER_HEADERS).json() == []


def test_a_declined_invitation_restores_their_previous_standing(client):
    _worked_here()
    invited = client.post(
        "/venues/me/people/worker-1/invite",
        json={"relationship_type": "bank"},
        headers=OPERATOR,
    ).json()

    declined = client.post(
        f"/me/invitations/{invited['relationship_id']}/decline", headers=WORKER_HEADERS
    )
    assert declined.status_code == 200, declined.text
    assert declined.json()["relationship_type"] == "one_off"
    assert declined.json()["status"] == "active"


def test_a_pool_member_who_declines_employment_stays_in_the_pool(client):
    _worked_here("pool")
    invited = client.post(
        "/venues/me/people/worker-1/invite",
        json={"relationship_type": "permanent"},
        headers=OPERATOR,
    ).json()
    assert invited["relationship_type"] == "pool"
    assert invited["status"] == "invited"

    pending = client.get("/me/invitations", headers=WORKER_HEADERS).json()
    assert [item["relationship_type"] for item in pending] == ["permanent"]

    declined = client.post(
        f"/me/invitations/{invited['relationship_id']}/decline", headers=WORKER_HEADERS
    )
    assert declined.status_code == 200, declined.text
    assert (declined.json()["relationship_type"], declined.json()["status"]) == ("pool", "active")


def test_an_invitation_from_scratch_declined_leaves_no_standing(client):
    invited = client.post(
        "/venues/me/people/worker-1/invite",
        json={"relationship_type": "permanent"},
        headers=OPERATOR,
    ).json()
    assert (invited["relationship_type"], invited["status"]) == ("one_off", "invited")

    declined = client.post(
        f"/me/invitations/{invited['relationship_id']}/decline", headers=WORKER_HEADERS
    )
    assert declined.json()["status"] == "ended"


def test_terms_can_be_set_on_active_employment_only(client):
    _worked_here()
    invited = client.post(
        "/venues/me/people/worker-1/invite",
        json={"relationship_type": "permanent"},
        headers=OPERATOR,
    ).json()
    refused = client.put(
        "/venues/me/people/worker-1/terms",
        json={"agreed_rate": "13.50"},
        headers=OPERATOR,
    )
    assert refused.status_code == 400

    client.post(f"/me/invitations/{invited['relationship_id']}/accept", headers=WORKER_HEADERS)
    updated = client.put(
        "/venues/me/people/worker-1/terms",
        json={"agreed_rate": "13.50", "contracted_hours_per_week": "30"},
        headers=OPERATOR,
    )
    assert updated.status_code == 200, updated.text
    assert updated.json()["agreed_rate"] == "13.50"
    assert updated.json()["contracted_hours_per_week"] == "30"


def test_an_invitation_cannot_be_answered_twice(client):
    _worked_here()
    invited = client.post(
        "/venues/me/people/worker-1/invite",
        json={"relationship_type": "permanent"},
        headers=OPERATOR,
    ).json()
    client.post(f"/me/invitations/{invited['relationship_id']}/accept", headers=WORKER_HEADERS)

    again = client.post(f"/me/invitations/{invited['relationship_id']}/accept", headers=WORKER_HEADERS)
    assert again.status_code == 400
    assert "already been answered" in again.text


def test_a_worker_cannot_accept_someone_elses_invitation(client):
    _worked_here()
    invited = client.post(
        "/venues/me/people/worker-1/invite",
        json={"relationship_type": "permanent"},
        headers=OPERATOR,
    ).json()

    intruder = {"X-Actor-Role": "worker", "X-Actor-Id": "worker-9"}
    response = client.post(f"/me/invitations/{invited['relationship_id']}/accept", headers=intruder)
    assert response.status_code == 404

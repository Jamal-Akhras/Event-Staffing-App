from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient

from apps.api.src import main
from apps.api.src.models.account import Account
from apps.api.src.models.worker_profile import WorkerProfile
from apps.api.src.models.worker_relationship import WorkerRelationship
from apps.api.src.repository_dependencies import (
    get_account_repo,
    get_notification_repo,
    get_shift_repo,
)
from apps.api.src.repository_dependencies_workforce import (
    shared_relationship_transition_repository,
    shared_worker_relationship_repository,
)
from apps.api.src.services.escalation_service import EscalationService
from apps.api.src.services.escalation_policy import EscalationPolicy, next_timestamps

VENUE_ID = "venue-1"
NOW = datetime(2030, 6, 1, 9, 0, tzinfo=UTC)
OPERATOR = {"X-Actor-Role": "operator", "X-Actor-Id": "operator-1", "X-Account-Id": VENUE_ID}
POOL_WORKER = {"X-Actor-Role": "worker", "X-Actor-Id": "pool-worker"}
STRANGER = {"X-Actor-Role": "worker", "X-Actor-Id": "stranger"}


@pytest.fixture(autouse=True)
def clear_state():
    for repo in (shared_worker_relationship_repository(), shared_relationship_transition_repository()):
        repo.clear()
    yield
    for repo in (shared_worker_relationship_repository(), shared_relationship_transition_repository()):
        repo.clear()


@pytest.fixture()
def client(in_memory_repos):
    in_memory_repos[get_account_repo].save(
        Account(
            account_id=VENUE_ID,
            name="The Grapes",
            country="GB",
            currency="GBP",
            created_at=NOW,
            market_id="bath-gb",
        )
    )
    from apps.api.src.models.organisation import Venue
    from apps.api.src.repository_dependencies import get_organisation_repo, get_worker_profile_repo

    in_memory_repos[get_organisation_repo].save_venue(
        Venue(
            venue_id=VENUE_ID,
            organisation_id="org-1",
            name="The Grapes",
            country="GB",
            currency="GBP",
            created_at=NOW,
            market_id="bath-gb",
        )
    )

    for worker_id in ("pool-worker", "stranger"):
        in_memory_repos[get_worker_profile_repo].save(
            WorkerProfile(
                worker_id=worker_id,
                display_name=worker_id,
                role="Bartender",
                city="Bath",
                experience_years=1,
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
                market_id="bath-gb",
            )
        )
    shared_worker_relationship_repository().save(
        WorkerRelationship(
            relationship_id="rel-pool",
            venue_id=VENUE_ID,
            worker_id="pool-worker",
            relationship_type="pool",
            status="active",
            created_at=NOW,
            updated_at=NOW,
        )
    )
    shared_worker_relationship_repository().save(
        WorkerRelationship(
            relationship_id="rel-stranger",
            venue_id=VENUE_ID,
            worker_id="stranger",
            relationship_type="one_off",
            status="active",
            created_at=NOW,
            updated_at=NOW,
        )
    )
    return TestClient(main.app)


def _create_shift(client: TestClient, hours_ahead: int = 24 * 14, **overrides) -> dict:
    start = NOW + timedelta(hours=hours_ahead)
    payload = {
        "role": "Bartender",
        "location": "Main bar",
        "start_time": start.isoformat(),
        "end_time": (start + timedelta(hours=5)).isoformat(),
        "pay_rate": 14.5,
        "workers_needed": 1,
        "now": NOW.isoformat(),
    }
    payload.update(overrides)
    response = client.post("/shifts", json=payload, headers={**OPERATOR, "X-Actor-Verified": "true"})
    assert response.status_code == 200, response.text
    return response.json()


def _service(repos) -> EscalationService:
    from apps.api.src.services.email import LoggingEmailTransport
    from apps.api.src.services.outbox_publisher import InMemoryOutboxPublisher

    return EscalationService(
        repos[get_shift_repo],
        shared_worker_relationship_repository(),
        repos[get_account_repo],
        InMemoryOutboxPublisher(repos[get_notification_repo], LoggingEmailTransport()),
    )


def test_a_new_shift_starts_with_the_venues_own_people(client):
    shift = _create_shift(client)
    assert shift["origin"] == "pool"
    assert shift["offer_pool_at"] is not None
    assert shift["publish_market_at"] is not None


def test_an_assigned_shift_starts_on_the_first_rung(client):
    shift = _create_shift(client, assigned_worker_id="pool-worker")
    assert shift["origin"] == "assigned"
    assert shift["assigned_worker_id"] == "pool-worker"


def test_a_pool_shift_reaches_a_pool_member_and_not_a_stranger(client):
    _create_shift(client)
    mine = client.get("/workers/me/feed", headers=POOL_WORKER).json()
    others = client.get("/workers/me/feed", headers=STRANGER).json()
    assert len(mine["items"]) == 1
    assert others["items"] == []


def test_an_assigned_shift_reaches_only_the_assigned_worker(client):
    _create_shift(client, assigned_worker_id="stranger")
    assigned = client.get("/workers/me/feed", headers=STRANGER).json()
    pool = client.get("/workers/me/feed", headers=POOL_WORKER).json()
    assert len(assigned["items"]) == 1
    assert pool["items"] == []


def test_the_sweep_moves_a_due_shift_one_rung_and_is_idempotent(client, in_memory_repos):
    shift = _create_shift(client, hours_ahead=24 * 14)
    service = _service(in_memory_repos)

    due = NOW + timedelta(hours=25)
    moved = service.sweep(due)
    assert [item.shift_id for item in moved] == [shift["shift_id"]]
    assert in_memory_repos[get_shift_repo].get(shift["shift_id"]).origin == "market"
    assert service.sweep(due) == []


def test_a_shift_with_the_market_rung_off_never_leaves_the_pool(client, in_memory_repos):
    accounts = in_memory_repos[get_account_repo]
    from dataclasses import replace

    accounts.save(replace(accounts.get(VENUE_ID), escalation_policy={"market_lead_hours": None}))
    shift = _create_shift(client)
    assert shift["publish_market_at"] is None

    service = _service(in_memory_repos)
    assert service.sweep(NOW + timedelta(days=300)) == []


def test_a_dropped_slot_restarts_the_ladder(client, in_memory_repos):
    shift = _create_shift(client, assigned_worker_id="pool-worker")
    service = _service(in_memory_repos)

    dropped_at = NOW + timedelta(days=2)
    restarted = service.restart_ladder(shift["shift_id"], dropped_at)
    assert restarted.origin == "pool"
    assert restarted.assigned_worker_id is None
    assert restarted.offer_pool_at == dropped_at
    assert restarted.publish_market_at > dropped_at


def test_an_assigned_shift_with_the_pool_rung_off_escalates_straight_to_market(client, in_memory_repos):
    from dataclasses import replace

    accounts = in_memory_repos[get_account_repo]
    accounts.save(replace(accounts.get(VENUE_ID), escalation_policy={"pool_hours": None}))
    shift = _create_shift(client, assigned_worker_id="pool-worker")
    assert shift["offer_pool_at"] is None
    assert shift["publish_market_at"] is not None

    service = _service(in_memory_repos)
    moved = service.sweep(NOW + timedelta(days=13))
    assert [item.origin for item in moved] == ["market"]


def test_a_shift_assigned_to_an_employee_is_not_billable(client, in_memory_repos):
    shared_worker_relationship_repository().save(
        WorkerRelationship(
            relationship_id="rel-pool",
            venue_id=VENUE_ID,
            worker_id="pool-worker",
            relationship_type="permanent",
            status="active",
            created_at=NOW,
            updated_at=NOW,
        )
    )
    shift = _create_shift(client, assigned_worker_id="pool-worker")
    assert in_memory_repos[get_shift_repo].get(shift["shift_id"]).billable is False


def test_a_shift_assigned_to_a_pool_member_stays_billable(client, in_memory_repos):
    shift = _create_shift(client, assigned_worker_id="pool-worker")
    assert in_memory_repos[get_shift_repo].get(shift["shift_id"]).billable is True


def test_assigning_a_worker_with_no_standing_is_refused(client):
    start = NOW + timedelta(days=14)
    response = client.post(
        "/shifts",
        json={
            "role": "Bartender",
            "location": "Main bar",
            "start_time": start.isoformat(),
            "end_time": (start + timedelta(hours=5)).isoformat(),
            "pay_rate": 14.5,
            "workers_needed": 1,
            "assigned_worker_id": "nobody",
            "now": NOW.isoformat(),
        },
        headers={**OPERATOR, "X-Actor-Verified": "true"},
    )
    assert response.status_code == 400
    assert "active relationship" in response.text


def test_a_vacated_market_slot_goes_back_to_the_venues_people(client, in_memory_repos):
    shift = _create_shift(client)
    client.post(
        f"/shifts/{shift['shift_id']}/advance",
        json={"target": "market", "now": NOW.isoformat()},
        headers=OPERATOR,
    )
    service = _service(in_memory_repos)
    restarted = service.restart_ladder(shift["shift_id"], NOW + timedelta(days=1))
    assert restarted.origin == "pool"


def test_a_drop_on_the_day_reaches_the_market_at_once():
    start = NOW + timedelta(hours=3)
    stamps = next_timestamps(start, NOW, EscalationPolicy(), assigned=False)
    assert stamps.publish_market_at == NOW


def test_the_venue_can_publish_to_market_without_waiting(client):
    shift = _create_shift(client)
    response = client.post(
        f"/shifts/{shift['shift_id']}/advance",
        json={"target": "market", "now": NOW.isoformat()},
        headers=OPERATOR,
    )
    assert response.status_code == 200, response.text
    assert response.json()["origin"] == "market"
    assert client.get("/workers/me/feed", headers=STRANGER).json()["items"] != []


def test_a_market_shift_cannot_be_advanced_further(client):
    shift = _create_shift(client)
    client.post(f"/shifts/{shift['shift_id']}/advance", json={"target": "market"}, headers=OPERATOR)
    again = client.post(f"/shifts/{shift['shift_id']}/advance", json={"target": "market"}, headers=OPERATOR)
    assert again.status_code == 400
    assert "already on the open market" in again.text


def test_another_venue_cannot_advance_the_shift(client):
    shift = _create_shift(client)
    other = {"X-Actor-Role": "operator", "X-Actor-Id": "operator-2", "X-Account-Id": "venue-2"}
    response = client.post(f"/shifts/{shift['shift_id']}/advance", json={"target": "market"}, headers=other)
    assert response.status_code == 404


def test_reaching_the_pool_notifies_pool_members_only(client, in_memory_repos):
    shift = _create_shift(client, assigned_worker_id="stranger")
    service = _service(in_memory_repos)
    service.sweep(NOW + timedelta(hours=25))

    notifications = in_memory_repos[get_notification_repo].list_for_worker("pool-worker", limit=10)
    assert [item.type for item in notifications] == ["shift.offered_to_pool"]
    assert in_memory_repos[get_notification_repo].list_for_worker("stranger", limit=10) == []


def _apply(client, shift_id, headers):
    worker_id = headers["X-Actor-Id"]
    return client.post(
        "/applications",
        json={"shift_id": shift_id, "worker_id": worker_id, "now": NOW.isoformat()},
        headers=headers,
    )


def test_an_unrelated_worker_cannot_apply_to_a_pool_shift(client):
    shift = _create_shift(client)
    refused = _apply(client, shift["shift_id"], STRANGER)
    assert refused.status_code == 403
    assert "not open to you" in refused.text

    allowed = _apply(client, shift["shift_id"], POOL_WORKER)
    assert allowed.status_code == 200, allowed.text


def test_only_the_assignee_can_apply_to_an_assigned_shift(client):
    shift = _create_shift(client, assigned_worker_id="pool-worker")
    assert _apply(client, shift["shift_id"], STRANGER).status_code == 403
    assert _apply(client, shift["shift_id"], POOL_WORKER).status_code == 200


def test_the_worker_shift_list_shows_only_what_reaches_them(client):
    shift = _create_shift(client)
    listed = client.get("/shifts", headers=STRANGER).json()
    assert shift["shift_id"] not in [item["shift_id"] for item in listed]

    client.post(
        f"/shifts/{shift['shift_id']}/advance",
        json={"target": "market", "now": NOW.isoformat()},
        headers=OPERATOR,
    )
    listed = client.get("/shifts", headers=STRANGER).json()
    assert shift["shift_id"] in [item["shift_id"] for item in listed]


def test_shift_detail_is_hidden_from_ineligible_workers(client):
    shift = _create_shift(client)
    assert client.get(f"/shifts/{shift['shift_id']}", headers=STRANGER).status_code == 404
    assert client.get(f"/shifts/{shift['shift_id']}", headers=POOL_WORKER).status_code == 200


def test_template_generated_shifts_follow_the_escalation_policy(client, in_memory_repos):
    from apps.api.src.repository_dependencies import get_template_repo
    from apps.api.src.schemas import GenerateShiftsRequest, TemplateCreateRequest
    from apps.api.src.services.template_service import TemplateService

    service = TemplateService(
        in_memory_repos[get_template_repo],
        in_memory_repos[get_shift_repo],
        _service(in_memory_repos),
    )
    template = service.create_template(
        TemplateCreateRequest(
            name="Friday bar",
            role="Bartender",
            location="Main bar",
            duration_hours=5,
            pay_rate=14.5,
            workers_needed=1,
        ),
        "operator-1",
        account_id=VENUE_ID,
    )
    generated = service.generate_shifts(
        template.template_id,
        GenerateShiftsRequest(
            start_date=NOW + timedelta(days=14),
            end_date=NOW + timedelta(days=14),
            start_time="18:00",
        ),
        "operator-1",
    )
    assert len(generated) == 1
    assert generated[0].origin == "pool"
    assert generated[0].offer_pool_at is not None
    assert generated[0].publish_market_at is not None


def _draft_shift(client, worker_id="pool-worker", hours_ahead=24 * 14):
    return _create_shift(
        client, hours_ahead=hours_ahead, assigned_worker_id=worker_id, rota_state="draft"
    )


def test_a_draft_shift_is_invisible_at_every_door(client):
    shift = _draft_shift(client)
    assert shift["rota_state"] == "draft"
    assert shift["offer_pool_at"] is None and shift["publish_market_at"] is None

    feed = client.get("/workers/me/feed", headers=POOL_WORKER).json()
    assert shift["shift_id"] not in [item["shift"]["shift_id"] for item in feed["items"]]
    listed = client.get("/shifts", headers=POOL_WORKER).json()
    assert shift["shift_id"] not in [item["shift_id"] for item in listed]
    assert client.get(f"/shifts/{shift['shift_id']}", headers=POOL_WORKER).status_code == 404
    assert _apply(client, shift["shift_id"], POOL_WORKER).status_code == 403


def test_a_draft_never_escalates(client, in_memory_repos):
    _draft_shift(client)
    service = _service(in_memory_repos)
    assert service.sweep(NOW + timedelta(days=300)) == []


def test_a_draft_requires_one_assigned_worker(client):
    start = NOW + timedelta(days=14)
    payload = {
        "role": "Bartender",
        "location": "Main bar",
        "start_time": start.isoformat(),
        "end_time": (start + timedelta(hours=5)).isoformat(),
        "pay_rate": 14.5,
        "workers_needed": 2,
        "assigned_worker_id": "pool-worker",
        "rota_state": "draft",
        "now": NOW.isoformat(),
    }
    response = client.post("/shifts", json=payload, headers={**OPERATOR, "X-Actor-Verified": "true"})
    assert response.status_code == 400
    assert "exactly one assigned worker" in response.text


def test_an_unassigned_shift_with_no_rung_available_is_refused(client, in_memory_repos):
    from dataclasses import replace

    accounts = in_memory_repos[get_account_repo]
    accounts.save(
        replace(accounts.get(VENUE_ID), escalation_policy={"pool_hours": None, "market_lead_hours": None})
    )
    start = NOW + timedelta(days=14)
    payload = {
        "role": "Bartender",
        "location": "Main bar",
        "start_time": start.isoformat(),
        "end_time": (start + timedelta(hours=5)).isoformat(),
        "pay_rate": 14.5,
        "workers_needed": 1,
        "now": NOW.isoformat(),
    }
    response = client.post("/shifts", json=payload, headers={**OPERATOR, "X-Actor-Verified": "true"})
    assert response.status_code == 400
    assert "nowhere to go" in response.text


def test_a_dropped_slot_with_no_rung_parks_privately(client, in_memory_repos):
    from dataclasses import replace

    shift = _create_shift(client, assigned_worker_id="pool-worker")
    accounts = in_memory_repos[get_account_repo]
    accounts.save(
        replace(accounts.get(VENUE_ID), escalation_policy={"pool_hours": None, "market_lead_hours": None})
    )
    service = _service(in_memory_repos)
    parked = service.restart_ladder(shift["shift_id"], NOW + timedelta(days=1))
    assert parked.needs_attention is True
    assert parked.offer_pool_at is None and parked.publish_market_at is None

    feed = client.get("/workers/me/feed", headers=POOL_WORKER).json()
    assert parked.shift_id not in [item["shift"]["shift_id"] for item in feed["items"]]
    assert client.get(f"/shifts/{parked.shift_id}", headers=POOL_WORKER).status_code == 404
    assert service.sweep(NOW + timedelta(days=300)) == []

    notifications = in_memory_repos[get_notification_repo].list_for_recipient("venue", VENUE_ID, 10)
    assert any(item.type == "shift.needs_attention" for item in notifications)

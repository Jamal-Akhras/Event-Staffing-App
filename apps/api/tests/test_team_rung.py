from dataclasses import replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient

from apps.api.src import main
from apps.api.src.models.account import Account
from apps.api.src.models.organisation import Venue
from apps.api.src.models.shift import Shift
from apps.api.src.models.worker_profile import WorkerProfile
from apps.api.src.models.worker_relationship import WorkerRelationship
from apps.api.src.repository_dependencies import (
    get_account_repo,
    get_notification_repo,
    get_organisation_repo,
    get_shift_repo,
    get_worker_profile_repo,
)
from apps.api.src.repository_dependencies_workforce import shared_worker_relationship_repository
from apps.api.src.services.errors import ValidationError
from apps.api.tests.test_gap_escalation import _service

VENUE_ID = "venue-1"
NOW = datetime(2030, 6, 1, 9, 0, tzinfo=UTC)
START = NOW + timedelta(days=7)
POLICY = {"named_offer_hours": 24, "team_hours": 6, "pool_hours": 24, "market_lead_hours": 48}
EMPLOYEE = {"X-Actor-Role": "worker", "X-Actor-Id": "emp-1"}
POOLER = {"X-Actor-Role": "worker", "X-Actor-Id": "pool-1"}
STRANGER = {"X-Actor-Role": "worker", "X-Actor-Id": "stranger"}


@pytest.fixture(autouse=True)
def clear_state():
    shared_worker_relationship_repository().clear()
    yield
    shared_worker_relationship_repository().clear()


@pytest.fixture()
def client(in_memory_repos):
    in_memory_repos[get_organisation_repo].save_venue(
        Venue(
            venue_id=VENUE_ID, organisation_id="org-1", name="The Grapes", country="GB",
            currency="GBP", created_at=NOW, market_id="bath-gb",
        )
    )
    in_memory_repos[get_account_repo].save(
        Account(
            account_id=VENUE_ID, name="The Grapes", country="GB", currency="GBP",
            created_at=NOW, market_id="bath-gb", escalation_policy=POLICY,
        )
    )
    for worker_id in ("emp-1", "pool-1", "stranger"):
        in_memory_repos[get_worker_profile_repo].save(
            WorkerProfile(
                worker_id=worker_id, display_name=worker_id, role="Bartender", city="Bath",
                experience_years=1, reliability_score=1.0, badges=[], bio=None, languages=["en"],
                email=None, phone=None, address=None, emergency_contact=None, pay_rate=None,
                notes=None, updated_at=NOW, market_id="bath-gb",
            )
        )
    _relationship("emp-1", "permanent")
    _relationship("pool-1", "pool")
    return TestClient(main.app)


def _relationship(worker_id: str, relationship_type: str, status: str = "active") -> None:
    shared_worker_relationship_repository().save(
        WorkerRelationship(
            relationship_id=f"rel-{worker_id}",
            venue_id=VENUE_ID,
            worker_id=worker_id,
            relationship_type=relationship_type,
            status=status,
            created_at=NOW,
            updated_at=NOW,
        )
    )


def _open_shift(repos, shift_id: str = "shift-1") -> Shift:
    service = _service(repos)
    shift = Shift(
        shift_id=shift_id,
        operator_id="operator-1",
        account_id=VENUE_ID,
        role="Bartender",
        location="Main bar",
        start_time=START,
        end_time=START + timedelta(hours=5),
        pay_rate=Decimal("14.50"),
        notes=None,
        status="open",
        created_at=NOW,
        workers_needed=1,
        workers_filled=0,
    )
    return repos[get_shift_repo].save(service.stamp_new_shift(shift, NOW))


def test_an_unassigned_shift_starts_with_the_team_and_walks_outward(client, in_memory_repos):
    shift = _open_shift(in_memory_repos)
    assert shift.origin == "team"
    assert shift.offer_team_at == NOW
    assert shift.offer_pool_at == NOW + timedelta(hours=6)
    assert shift.publish_market_at == NOW + timedelta(hours=30)

    service = _service(in_memory_repos)
    assert service.sweep(NOW + timedelta(hours=5)) == []
    moved = service.sweep(NOW + timedelta(hours=6))
    assert [item.origin for item in moved] == ["pool"]
    pool_notes = in_memory_repos[get_notification_repo].list_for_worker("pool-1", limit=10)
    emp_notes = in_memory_repos[get_notification_repo].list_for_worker("emp-1", limit=10)
    assert any(note.type == "shift.offered_to_pool" for note in pool_notes)
    assert not any(note.type == "shift.offered_to_pool" for note in emp_notes)

    moved = service.sweep(NOW + timedelta(hours=30))
    assert [item.origin for item in moved] == ["market"]


def test_a_team_shift_reaches_only_employed_staff(client, in_memory_repos):
    shift = _open_shift(in_memory_repos)
    assert shift.origin == "team"

    for headers, expected in ((EMPLOYEE, True), (POOLER, False), (STRANGER, False)):
        feed = client.get("/workers/me/feed?limit=20", headers=headers).json()
        seen = any(item["shift_id"] == shift.shift_id for item in feed["items"])
        assert seen is expected, headers

    assert client.get(f"/shifts/{shift.shift_id}", headers=EMPLOYEE).status_code == 200
    assert client.get(f"/shifts/{shift.shift_id}", headers=POOLER).status_code == 404

    refused = client.post(
        "/applications",
        json={"shift_id": shift.shift_id, "worker_id": "pool-1", "now": NOW.isoformat()},
        headers=POOLER,
    )
    assert refused.status_code in (400, 403, 404)


def test_manual_advance_only_moves_outward(client, in_memory_repos):
    shift = _open_shift(in_memory_repos)
    service = _service(in_memory_repos)

    advanced = service.advance_now(shift.shift_id, VENUE_ID, "market", NOW)
    assert advanced.origin == "market"
    with pytest.raises(ValidationError):
        service.advance_now(shift.shift_id, VENUE_ID, "pool", NOW)


def test_without_employees_the_team_rung_is_skipped(client, in_memory_repos):
    relationships = shared_worker_relationship_repository()
    relationships.save(replace(relationships.get("rel-emp-1"), status="ended"))

    shift = _open_shift(in_memory_repos)
    assert shift.origin == "pool"
    assert shift.offer_team_at is None
    assert shift.offer_pool_at == NOW

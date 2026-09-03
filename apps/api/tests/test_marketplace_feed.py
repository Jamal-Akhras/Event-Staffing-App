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
    get_organisation_repo,
    get_shift_repo,
    get_worker_profile_repo,
)
from apps.api.src.repository_dependencies_workforce import shared_worker_relationship_repository

NOW = datetime.now(UTC)
START = NOW + timedelta(days=3)
WORKER = {"X-Actor-Role": "worker", "X-Actor-Id": "worker-1"}


@pytest.fixture(autouse=True)
def clear_state():
    shared_worker_relationship_repository().clear()
    yield
    shared_worker_relationship_repository().clear()


@pytest.fixture()
def client(in_memory_repos):
    for venue_id, name in (("venue-open", "The Open Arms"), ("venue-pool", "The Pool House")):
        in_memory_repos[get_account_repo].save(
            Account(
                account_id=venue_id, name=name, country="GB", currency="GBP",
                created_at=NOW, market_id="bath-gb",
            )
        )
        in_memory_repos[get_organisation_repo].save_venue(
            Venue(
                venue_id=venue_id, organisation_id="org-1", name=name, country="GB",
                currency="GBP", created_at=NOW, market_id="bath-gb",
            )
        )
    in_memory_repos[get_worker_profile_repo].save(
        WorkerProfile(
            worker_id="worker-1", display_name="Alex", role="Bartender", city="Bath",
            experience_years=1, reliability_score=1.0, badges=[], bio=None, languages=["en"],
            email=None, phone=None, address=None, emergency_contact=None, pay_rate=None,
            notes=None, updated_at=NOW, market_id="bath-gb",
        )
    )
    shared_worker_relationship_repository().save(
        WorkerRelationship(
            relationship_id="rel-1",
            venue_id="venue-pool",
            worker_id="worker-1",
            relationship_type="pool",
            status="active",
            created_at=NOW,
            updated_at=NOW,
        )
    )

    def shift(shift_id: str, venue_id: str, origin: str, hour_offset: int, **overrides) -> None:
        values = dict(
            shift_id=shift_id,
            operator_id="operator-1",
            account_id=venue_id,
            role="Bartender",
            location="Main bar",
            start_time=START + timedelta(hours=hour_offset),
            end_time=START + timedelta(hours=hour_offset + 5),
            pay_rate=Decimal("14.50"),
            notes=None,
            status="open",
            created_at=NOW,
            workers_needed=1,
            workers_filled=0,
            origin=origin,
        )
        values.update(overrides)
        in_memory_repos[get_shift_repo].save(Shift(**values))

    shift("s-market-open", "venue-open", "market", 0)
    shift("s-market-pool-venue", "venue-pool", "market", 1)
    shift("s-pool", "venue-pool", "pool", 2)
    shift("s-assigned", "venue-open", "assigned", 3, assigned_worker_id="worker-1")
    return TestClient(main.app)


def _feed_ids(client: TestClient) -> set[str]:
    body = client.get("/workers/me/feed?limit=20", headers=WORKER).json()
    return {item["shift_id"] for item in body["items"]}


def test_disabling_the_marketplace_hides_only_unrelated_open_shifts(client):
    assert _feed_ids(client) == {"s-market-open", "s-market-pool-venue", "s-pool", "s-assigned"}

    response = client.put(
        "/me/work-preferences", json={"marketplace_enabled": False}, headers=WORKER
    )
    assert response.status_code == 200, response.text
    assert response.json() == {"marketplace_enabled": False}

    assert _feed_ids(client) == {"s-market-pool-venue", "s-pool", "s-assigned"}
    context = client.get("/me/work-context", headers=WORKER).json()
    assert context["marketplace_enabled"] is False

    client.put("/me/work-preferences", json={"marketplace_enabled": True}, headers=WORKER)
    assert _feed_ids(client) == {"s-market-open", "s-market-pool-venue", "s-pool", "s-assigned"}

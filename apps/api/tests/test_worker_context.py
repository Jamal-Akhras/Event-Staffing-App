from datetime import UTC, datetime
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient

from apps.api.src import main
from apps.api.src.models.account import Account
from apps.api.src.models.worker_relationship import WorkerRelationship
from apps.api.src.repository_dependencies import get_account_repo
from apps.api.src.repository_dependencies_workforce import shared_worker_relationship_repository

NOW = datetime(2030, 6, 3, 9, 0, tzinfo=UTC)
WORKER = {"X-Actor-Role": "worker", "X-Actor-Id": "worker-1"}
OPERATOR = {"X-Actor-Role": "operator", "X-Actor-Id": "operator-1", "X-Account-Id": "venue-1"}


@pytest.fixture(autouse=True)
def clear_state():
    shared_worker_relationship_repository().clear()
    yield
    shared_worker_relationship_repository().clear()


@pytest.fixture()
def client(in_memory_repos):
    in_memory_repos[get_account_repo].save(
        Account(
            account_id="venue-1", name="The Grapes", country="GB", currency="GBP",
            created_at=NOW, market_id="bath-gb",
        )
    )
    return TestClient(main.app)


def _relationship(
    relationship_id: str, venue_id: str, relationship_type: str, status: str = "active",
    worker_id: str = "worker-1",
) -> None:
    shared_worker_relationship_repository().save(
        WorkerRelationship(
            relationship_id=relationship_id,
            venue_id=venue_id,
            worker_id=worker_id,
            relationship_type=relationship_type,
            status=status,
            created_at=NOW,
            updated_at=NOW,
            agreed_rate=Decimal("15.00") if relationship_type == "permanent" else None,
        )
    )


def test_a_worker_sees_their_relationships_with_venue_names(client):
    _relationship("rel-1", "venue-1", "permanent")
    _relationship("rel-2", "venue-unknown", "pool")
    _relationship("rel-other", "venue-1", "pool", worker_id="worker-2")

    body = client.get("/me/relationships", headers=WORKER).json()
    assert [(item["relationship_id"], item["venue_name"]) for item in body] == [
        ("rel-1", "The Grapes"),
        ("rel-2", None),
    ]
    assert body[0]["agreed_rate"] == "15.00"


def test_work_context_is_shifts_first_for_employed_workers(client):
    _relationship("rel-1", "venue-1", "permanent")
    _relationship("rel-2", "venue-2", "pool")

    body = client.get("/me/work-context", headers=WORKER).json()
    assert body == {
        "home_mode": "shifts",
        "employed": True,
        "active_relationships": 2,
        "marketplace_enabled": True,
    }


def test_work_context_is_browse_first_without_employment(client):
    _relationship("rel-1", "venue-1", "pool")
    _relationship("rel-2", "venue-2", "permanent", status="invited")

    body = client.get("/me/work-context", headers=WORKER).json()
    assert body == {
        "home_mode": "browse",
        "employed": False,
        "active_relationships": 1,
        "marketplace_enabled": True,
    }


def test_a_worker_with_no_relationships_lands_on_browse(client):
    body = client.get("/me/work-context", headers=WORKER).json()
    assert body == {
        "home_mode": "browse",
        "employed": False,
        "active_relationships": 0,
        "marketplace_enabled": True,
    }
    assert client.get("/me/relationships", headers=WORKER).json() == []


def test_worker_context_is_worker_only(client):
    assert client.get("/me/relationships", headers=OPERATOR).status_code == 403
    assert client.get("/me/work-context", headers=OPERATOR).status_code == 403

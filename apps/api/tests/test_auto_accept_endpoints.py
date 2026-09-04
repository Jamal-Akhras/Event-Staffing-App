from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient

from apps.api.src import main, repository_dependencies as rd
from apps.api.src.models.auto_accept import AutoAcceptAttempt
from apps.api.src.models.shift_offer import ShiftOffer
from apps.api.src.models.worker_relationship import WorkerRelationship
from apps.api.src.repository_dependencies_workforce import (
    shared_worker_relationship_repository,
)

NOW = datetime(2030, 6, 3, 9, 0, tzinfo=UTC)
WORKER = {"X-Actor-Role": "worker", "X-Actor-Id": "worker-1"}
OTHER_WORKER = {"X-Actor-Role": "worker", "X-Actor-Id": "worker-2"}


def _relationship(worker_id: str = "worker-1", venue_id: str = "venue-1") -> None:
    shared_worker_relationship_repository().save(
        WorkerRelationship(
            relationship_id=f"rel-{worker_id}-{venue_id}",
            venue_id=venue_id,
            worker_id=worker_id,
            relationship_type="pool",
            status="active",
            created_at=NOW,
            updated_at=NOW,
        )
    )


def _attempt(worker_id: str, offer_id: str, minute: int) -> None:
    rd._SHIFT_OFFERS.save(
        ShiftOffer(
            offer_id=offer_id,
            shift_id=f"shift-{offer_id}",
            venue_id="venue-1",
            worker_id=worker_id,
            source="rota",
            status="pending",
            offered_at=NOW,
        )
    )
    rd._AUTO_ACCEPT_ATTEMPTS.save(
        AutoAcceptAttempt(
            attempt_id=f"attempt-{offer_id}",
            offer_id=offer_id,
            rule_id="rule-1",
            rule_version=1,
            rule_snapshot={"enabled": True, "roles": []},
            evaluated_at=NOW + timedelta(minutes=minute),
            outcome="skipped",
            reason="role_mismatch",
        )
    )


def test_worker_rule_routes_cover_put_get_delete_and_foreign_scope(in_memory_repos):
    client = TestClient(main.app)
    _relationship()
    payload = {
        "enabled": True,
        "roles": [" Bartender "],
        "minimum_rate": "13.50",
        "minimum_notice_hours": 12,
        "now": NOW.isoformat(),
    }

    created = client.put(
        "/me/auto-accept-rules/venue-1", json=payload, headers=WORKER
    )

    assert created.status_code == 200, created.text
    assert created.json()["roles"] == ["Bartender"]
    assert created.json()["version"] == 1
    listed = client.get("/me/auto-accept-rules", headers=WORKER)
    assert listed.status_code == 200
    assert [item["venue_id"] for item in listed.json()] == ["venue-1"]
    assert client.get("/me/auto-accept-rules", headers=OTHER_WORKER).json() == []

    foreign = client.put(
        "/me/auto-accept-rules/venue-foreign",
        json={**payload, "enabled": False},
        headers=WORKER,
    )
    assert foreign.status_code == 404
    assert (
        client.delete("/me/auto-accept-rules/venue-foreign", headers=WORKER).status_code
        == 404
    )

    deleted = client.delete("/me/auto-accept-rules/venue-1", headers=WORKER)
    assert deleted.status_code == 204
    assert client.get("/me/auto-accept-rules", headers=WORKER).json() == []


def test_attempt_route_is_newest_first_limited_and_worker_scoped(in_memory_repos):
    client = TestClient(main.app)
    _attempt("worker-1", "offer-old", 1)
    _attempt("worker-1", "offer-new", 2)
    _attempt("worker-2", "offer-other", 3)

    response = client.get("/me/auto-accept-attempts?limit=1", headers=WORKER)

    assert response.status_code == 200
    assert [item["offer_id"] for item in response.json()] == ["offer-new"]
    other = client.get("/me/auto-accept-attempts", headers=OTHER_WORKER)
    assert [item["offer_id"] for item in other.json()] == ["offer-other"]

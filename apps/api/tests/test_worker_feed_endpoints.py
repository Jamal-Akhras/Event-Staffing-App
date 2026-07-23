from datetime import datetime, timedelta

from fastapi.testclient import TestClient

from apps.api.src import main
from apps.api.src.deps import get_shift_repo, get_worker_feed_state_repo
from apps.api.src.repositories.in_memory_shift_repository import InMemoryShiftRepository
from apps.api.src.repositories.in_memory_worker_feed_state_repository import (
    InMemoryWorkerFeedStateRepository,
)


def _client() -> TestClient:
    shift_repo = InMemoryShiftRepository()
    feed_repo = InMemoryWorkerFeedStateRepository()
    main.app.dependency_overrides.clear()
    main.app.dependency_overrides[get_shift_repo] = lambda: shift_repo
    main.app.dependency_overrides[get_worker_feed_state_repo] = lambda: feed_repo
    return TestClient(main.app)


def test_worker_feed_state_round_trip_and_delete():
    client = _client()
    shift_id = _create_shift(client)
    headers = {"X-Actor-Role": "worker", "X-Actor-Id": "worker-1"}

    saved = client.put(
        f"/workers/worker-1/feed-state/{shift_id}",
        json={"action": "passed"},
        headers=headers,
    )
    assert saved.status_code == 200
    assert saved.json()["shift_id"] == shift_id
    assert saved.json()["action"] == "passed"

    listed = client.get("/workers/worker-1/feed-state", headers=headers)
    assert listed.status_code == 200
    assert [item["shift_id"] for item in listed.json()] == [shift_id]

    deleted = client.delete(f"/workers/worker-1/feed-state/{shift_id}", headers=headers)
    assert deleted.status_code == 200

    empty = client.get("/workers/worker-1/feed-state", headers=headers)
    assert empty.status_code == 200
    assert empty.json() == []


def test_worker_feed_state_is_worker_owned():
    client = _client()
    shift_id = _create_shift(client)

    response = client.put(
        f"/workers/worker-1/feed-state/{shift_id}",
        json={"action": "passed"},
        headers={"X-Actor-Role": "worker", "X-Actor-Id": "worker-2"},
    )

    assert response.status_code == 403


def _create_shift(client: TestClient) -> str:
    now = datetime(2030, 1, 1, 9, 0, 0)
    response = client.post(
        "/shifts",
        json={
            "role": "server",
            "location": "Downtown",
            "start_time": (now + timedelta(days=1)).isoformat(),
            "end_time": (now + timedelta(days=1, hours=4)).isoformat(),
            "pay_rate": 25.0,
            "now": now.isoformat(),
        },
        headers={"X-Actor-Role": "operator", "X-Actor-Id": "operator-1"},
    )
    assert response.status_code == 200
    return response.json()["shift_id"]

from datetime import UTC, datetime

from fastapi.testclient import TestClient

from apps.api.src import main
from apps.api.src.deps import get_worker_profile_repo
from apps.api.src.repositories.in_memory_worker_profile_repository import (
    InMemoryWorkerProfileRepository,
)

OPERATOR_HEADERS = {"X-Actor-Role": "operator", "X-Actor-Id": "operator-1"}
WORKER_HEADERS = {"X-Actor-Role": "worker", "X-Actor-Id": "worker-1"}
OTHER_WORKER_HEADERS = {"X-Actor-Role": "worker", "X-Actor-Id": "worker-2"}


def _client() -> TestClient:
    repo = InMemoryWorkerProfileRepository()
    main.app.dependency_overrides[get_worker_profile_repo] = lambda: repo
    return TestClient(main.app)


def test_worker_profile_update_and_public_view():
    client = _client()
    now = datetime(2030, 1, 1, 9, 0, 0, tzinfo=UTC)
    payload = {
        "display_name": "Alex",
        "role": "server",
        "city": "Austin",
        "experience_years": 3,
        "bio": "Night shift",
        "languages": ["English", "Spanish"],
        "email": "alex@example.com",
        "phone": "555-0100",
        "address": "123 Main",
        "emergency_contact": "Jordan",
        "pay_rate": 24.5,
        "notes": "Prefers weekends",
        "now": now.isoformat(),
    }
    update = client.put(
        "/workers/worker-1",
        json=payload,
        headers=WORKER_HEADERS,
    )
    assert update.status_code == 200
    assert update.json()["display_name"] == "Alex"

    public = client.get(
        "/workers/worker-1",
        headers=OPERATOR_HEADERS,
    )
    assert public.status_code == 200
    assert public.json()["email"] is None
    assert public.json()["phone"] is None

    private = client.get("/workers/worker-1", headers=WORKER_HEADERS)
    assert private.status_code == 200
    assert private.json()["email"] == "alex@example.com"

    forbidden = client.get("/workers/worker-1", headers=OTHER_WORKER_HEADERS)
    assert forbidden.status_code == 403

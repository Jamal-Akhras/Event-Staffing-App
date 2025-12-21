from datetime import datetime, timedelta

from fastapi.testclient import TestClient

from apps.api.src import main
from apps.api.src.deps import get_shift_repo
from apps.api.src.repositories.in_memory_shift_repository import InMemoryShiftRepository


def _client() -> TestClient:
    shift_repo = InMemoryShiftRepository()
    main.app.dependency_overrides[get_shift_repo] = lambda: shift_repo
    return TestClient(main.app)


def test_shift_create_and_list():
    client = _client()
    now = datetime(2030, 1, 1, 9, 0, 0)
    start = now + timedelta(hours=2)
    end = start + timedelta(hours=4)

    create = client.post(
        "/shifts",
        json={
            "operator_id": "operator-1",
            "role": "server",
            "location": "Downtown",
            "start_time": start.isoformat(),
            "end_time": end.isoformat(),
            "pay_rate": 25.0,
            "notes": "Black shirt",
            "now": now.isoformat(),
        },
        headers={"X-Actor-Role": "operator"},
    )
    assert create.status_code == 200

    listed = client.get("/shifts", headers={"X-Actor-Role": "worker"})
    assert listed.status_code == 200
    assert listed.json()[0]["role"] == "server"

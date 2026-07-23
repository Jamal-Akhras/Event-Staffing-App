from datetime import datetime, timedelta

from fastapi.testclient import TestClient

from apps.api.src import main
from apps.api.src.deps import get_shift_repo
from apps.api.src.repositories.in_memory_shift_repository import InMemoryShiftRepository

OPERATOR_HEADERS = {"X-Actor-Role": "operator", "X-Actor-Id": "operator-1"}
OTHER_OPERATOR_HEADERS = {"X-Actor-Role": "operator", "X-Actor-Id": "operator-2"}
WORKER_HEADERS = {"X-Actor-Role": "worker", "X-Actor-Id": "worker-1"}


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
        headers=OPERATOR_HEADERS,
    )
    assert create.status_code == 200

    listed = client.get("/shifts", headers=WORKER_HEADERS)
    assert listed.status_code == 200
    assert listed.json()[0]["role"] == "server"

    other_operator_list = client.get("/shifts", headers=OTHER_OPERATOR_HEADERS)
    assert other_operator_list.status_code == 200
    assert other_operator_list.json() == []

    other_operator_get = client.get(
        f"/shifts/{create.json()['shift_id']}",
        headers=OTHER_OPERATOR_HEADERS,
    )
    assert other_operator_get.status_code == 403

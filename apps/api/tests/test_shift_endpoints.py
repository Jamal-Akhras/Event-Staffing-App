from datetime import UTC, datetime, timedelta

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
    now = datetime(2030, 1, 1, 9, 0, 0, tzinfo=UTC)
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


def test_shift_create_rejects_timezone_less_timestamps():
    client = _client()
    response = client.post(
        "/shifts",
        json={
            "role": "server",
            "location": "Downtown",
            "start_time": "2030-01-01T11:00:00",
            "end_time": "2030-01-01T15:00:00",
            "pay_rate": 25,
        },
        headers=OPERATOR_HEADERS,
    )

    assert response.status_code == 422


def test_shift_create_normalizes_offset_timestamps_to_utc():
    client = _client()
    response = client.post(
        "/shifts",
        json={
            "role": "server",
            "location": "Downtown",
            "start_time": "2030-06-01T11:00:00+01:00",
            "end_time": "2030-06-01T15:00:00+01:00",
            "pay_rate": 25,
        },
        headers=OPERATOR_HEADERS,
    )

    assert response.status_code == 200
    start_time = datetime.fromisoformat(response.json()["start_time"].replace("Z", "+00:00"))
    assert start_time == datetime(2030, 6, 1, 10, 0, tzinfo=UTC)


def test_shift_create_rejects_fractional_pennies():
    client = _client()
    response = client.post(
        "/shifts",
        json={
            "role": "server",
            "location": "Downtown",
            "start_time": "2030-01-01T11:00:00Z",
            "end_time": "2030-01-01T15:00:00Z",
            "pay_rate": 25.001,
        },
        headers=OPERATOR_HEADERS,
    )

    assert response.status_code == 422

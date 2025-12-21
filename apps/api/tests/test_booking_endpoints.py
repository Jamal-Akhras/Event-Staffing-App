from datetime import datetime, timedelta

from fastapi.testclient import TestClient

from apps.api.src import main
from apps.api.src.deps import get_booking_repo
from apps.api.src.repositories.in_memory_booking_repository import InMemoryBookingRepository


def _client() -> TestClient:
    repo = InMemoryBookingRepository()
    main.app.dependency_overrides[get_booking_repo] = lambda: repo
    return TestClient(main.app)


def _create_booking(client: TestClient, start_offset_minutes: int = 60) -> tuple[str, datetime]:
    now = datetime(2030, 1, 1, 12, 0, 0)
    start = now + timedelta(minutes=start_offset_minutes)
    end = start + timedelta(hours=4)
    response = client.post(
        "/bookings",
        json={
            "shift_id": "shift-1",
            "worker_id": "worker-1",
            "operator_id": "operator-1",
            "start_time": start.isoformat(),
            "end_time": end.isoformat(),
            "now": now.isoformat(),
        },
        headers={"X-Actor-Role": "operator"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert "allowed_transitions" in payload
    return payload["booking_id"], now


def test_booking_lifecycle_happy_path():
    client = _client()
    booking_id, now = _create_booking(client)

    confirm = client.post(
        f"/bookings/{booking_id}/confirm",
        json={"now": (now + timedelta(minutes=5)).isoformat()},
        headers={"X-Actor-Role": "operator"},
    )
    assert confirm.status_code == 200
    assert confirm.json()["state"] == "confirmed"

    check_in_time = now + timedelta(minutes=40)
    check_in = client.post(
        f"/bookings/{booking_id}/check-in",
        json={"now": check_in_time.isoformat()},
        headers={"X-Actor-Role": "worker"},
    )
    assert check_in.status_code == 200
    assert check_in.json()["state"] == "checked_in"

    check_out = client.post(
        f"/bookings/{booking_id}/check-out",
        json={"now": (check_in_time + timedelta(hours=4)).isoformat()},
        headers={"X-Actor-Role": "worker"},
    )
    assert check_out.status_code == 200
    assert check_out.json()["state"] == "checked_out"

    approve = client.post(
        f"/bookings/{booking_id}/approve",
        json={"now": (now + timedelta(hours=5)).isoformat()},
        headers={"X-Actor-Role": "operator"},
    )
    assert approve.status_code == 200
    assert approve.json()["state"] == "approved"

    pay = client.post(
        f"/bookings/{booking_id}/pay",
        json={"now": (now + timedelta(hours=6)).isoformat()},
        headers={"X-Actor-Role": "operator"},
    )
    assert pay.status_code == 200
    assert pay.json()["state"] == "paid"


def test_invalid_transition_returns_400():
    client = _client()
    booking_id, now = _create_booking(client)

    check_in = client.post(
        f"/bookings/{booking_id}/check-in",
        json={"now": (now + timedelta(minutes=10)).isoformat()},
        headers={"X-Actor-Role": "worker"},
    )
    assert check_in.status_code == 400


def test_no_show_requires_window_closed():
    client = _client()
    booking_id, now = _create_booking(client)
    client.post(
        f"/bookings/{booking_id}/confirm",
        json={"now": (now + timedelta(minutes=5)).isoformat()},
        headers={"X-Actor-Role": "operator"},
    )

    too_early = now + timedelta(minutes=70)
    response = client.post(
        f"/bookings/{booking_id}/no-show",
        json={"now": too_early.isoformat()},
        headers={"X-Actor-Role": "operator"},
    )
    assert response.status_code == 400

    after_close = now + timedelta(minutes=76)
    response = client.post(
        f"/bookings/{booking_id}/no-show",
        json={"now": after_close.isoformat()},
        headers={"X-Actor-Role": "operator"},
    )
    assert response.status_code == 200
    assert response.json()["state"] == "no_show"


def test_list_bookings_returns_recent():
    client = _client()
    booking_id, _ = _create_booking(client)
    response = client.get("/bookings", headers={"X-Actor-Role": "operator"})
    assert response.status_code == 200
    payload = response.json()
    assert isinstance(payload, list)
    assert payload[0]["booking_id"] == booking_id


def test_role_required():
    client = _client()
    response = client.get("/bookings")
    assert response.status_code == 401

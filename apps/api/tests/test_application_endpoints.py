from datetime import datetime, timedelta

from fastapi.testclient import TestClient

from apps.api.src import main
from apps.api.src.deps import get_application_repo, get_booking_repo, get_shift_repo
from apps.api.src.repositories.in_memory_application_repository import InMemoryApplicationRepository
from apps.api.src.repositories.in_memory_booking_repository import InMemoryBookingRepository
from apps.api.src.repositories.in_memory_shift_repository import InMemoryShiftRepository


def _client() -> TestClient:
    application_repo = InMemoryApplicationRepository()
    booking_repo = InMemoryBookingRepository()
    shift_repo = InMemoryShiftRepository()
    main.app.dependency_overrides[get_application_repo] = lambda: application_repo
    main.app.dependency_overrides[get_booking_repo] = lambda: booking_repo
    main.app.dependency_overrides[get_shift_repo] = lambda: shift_repo
    return TestClient(main.app)


def test_application_approve_creates_booking():
    client = _client()
    now = datetime(2030, 1, 1, 9, 0, 0)
    start = now + timedelta(hours=2)
    end = start + timedelta(hours=4)

    shift = client.post(
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
    assert shift.status_code == 200
    shift_id = shift.json()["shift_id"]

    response = client.post(
        "/applications",
        json={
            "shift_id": shift_id,
            "worker_id": "worker-1",
            "message": "available",
            "now": now.isoformat(),
        },
        headers={"X-Actor-Role": "worker"},
    )
    assert response.status_code == 200
    application_id = response.json()["application_id"]

    approve = client.post(
        f"/applications/{application_id}/approve",
        json={"now": now.isoformat()},
        headers={"X-Actor-Role": "operator"},
    )
    assert approve.status_code == 200
    payload = approve.json()
    assert payload["status"] == "approved"
    assert payload["booking_id"]

    bookings = client.get("/bookings", headers={"X-Actor-Role": "operator"})
    assert bookings.status_code == 200
    assert bookings.json()[0]["booking_id"] == payload["booking_id"]

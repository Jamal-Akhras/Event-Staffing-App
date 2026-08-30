from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient

from apps.api.src import main
from apps.api.src.deps import (
    get_application_decision_repo,
    get_application_repo,
    get_booking_charge_repo,
    get_booking_repo,
    get_booking_transition_repo,
    get_notification_repo,
    get_shift_repo,
)
from apps.api.src.repositories.in_memory_application_decision_repository import (
    InMemoryApplicationDecisionRepository,
)
from apps.api.src.repositories.in_memory_application_repository import InMemoryApplicationRepository
from apps.api.src.repositories.in_memory_booking_repository import InMemoryBookingRepository
from apps.api.src.repositories.in_memory_notification_repository import InMemoryNotificationRepository
from apps.api.src.repositories.in_memory_shift_repository import InMemoryShiftRepository
from apps.api.src.repository_dependencies import shared_booking_charge_repository, shared_booking_transition_repository


def _client() -> TestClient:
    application_repo = InMemoryApplicationRepository()
    booking_repo = InMemoryBookingRepository()
    shift_repo = InMemoryShiftRepository(booking_repo)
    application_repo.attach_shift_repo(shift_repo)
    booking_repo.attach_shift_repo(shift_repo)
    decision_repo = InMemoryApplicationDecisionRepository(
        application_repo,
        booking_repo,
        shift_repo,
    )
    main.app.dependency_overrides[get_application_repo] = lambda: application_repo
    main.app.dependency_overrides[get_booking_repo] = lambda: booking_repo
    main.app.dependency_overrides[get_booking_transition_repo] = shared_booking_transition_repository
    main.app.dependency_overrides[get_booking_charge_repo] = shared_booking_charge_repository
    main.app.dependency_overrides[get_shift_repo] = lambda: shift_repo
    main.app.dependency_overrides[get_application_decision_repo] = lambda: decision_repo
    main.app.dependency_overrides[get_notification_repo] = InMemoryNotificationRepository
    return TestClient(main.app)


def test_application_approve_creates_booking():
    client = _client()
    now = datetime(2030, 1, 1, 9, 0, 0, tzinfo=UTC)
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
        headers={"X-Actor-Role": "operator", "X-Actor-Id": "operator-1"},
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
        headers={"X-Actor-Role": "worker", "X-Actor-Id": "worker-1"},
    )
    assert response.status_code == 200
    application_id = response.json()["application_id"]

    approve = client.post(
        f"/applications/{application_id}/approve",
        json={"now": now.isoformat()},
        headers={"X-Actor-Role": "operator", "X-Actor-Id": "operator-1"},
    )
    assert approve.status_code == 200
    payload = approve.json()
    assert payload["status"] == "approved"
    assert payload["booking_id"]

    bookings = client.get("/bookings", headers={"X-Actor-Role": "operator", "X-Actor-Id": "operator-1"})
    assert bookings.status_code == 200
    assert bookings.json()[0]["booking_id"] == payload["booking_id"]


def test_worker_cannot_create_application_for_another_worker():
    client = _client()
    now = datetime(2030, 1, 1, 9, 0, 0, tzinfo=UTC)
    start = now + timedelta(hours=2)
    end = start + timedelta(hours=4)

    shift = client.post(
        "/shifts",
        json={
            "role": "server",
            "location": "Downtown",
            "start_time": start.isoformat(),
            "end_time": end.isoformat(),
            "pay_rate": 25.0,
            "now": now.isoformat(),
        },
        headers={"X-Actor-Role": "operator", "X-Actor-Id": "operator-1"},
    )
    assert shift.status_code == 200

    response = client.post(
        "/applications",
        json={
            "shift_id": shift.json()["shift_id"],
            "worker_id": "worker-1",
            "message": "available",
            "now": now.isoformat(),
        },
        headers={"X-Actor-Role": "worker", "X-Actor-Id": "worker-2"},
    )

    assert response.status_code == 403

"""Tests for multi-worker shift capacity."""

from datetime import datetime, timedelta

import pytest
from fastapi.testclient import TestClient

from apps.api.src.deps import (
    get_application_decision_repo,
    get_application_repo,
    get_booking_repo,
    get_shift_repo,
)
from apps.api.src.main import app
from apps.api.src.repositories.in_memory_application_decision_repository import (
    InMemoryApplicationDecisionRepository,
)
from apps.api.src.repositories.in_memory_application_repository import (
    InMemoryApplicationRepository,
)
from apps.api.src.repositories.in_memory_booking_repository import InMemoryBookingRepository
from apps.api.src.repositories.in_memory_shift_repository import InMemoryShiftRepository

client = TestClient(app)
OPERATOR_HEADERS = {"X-Actor-Role": "operator", "X-Actor-Id": "op-test"}
WORKER_HEADERS = {"X-Actor-Role": "worker", "X-Actor-Id": "worker-test"}


@pytest.fixture
def repos():
    booking_repo = InMemoryBookingRepository()
    shift_repo = InMemoryShiftRepository(booking_repo)
    application_repo = InMemoryApplicationRepository()
    application_repo.attach_shift_repo(shift_repo)
    booking_repo.attach_shift_repo(shift_repo)
    decision_repo = InMemoryApplicationDecisionRepository(
        application_repo,
        booking_repo,
        shift_repo,
    )
    app.dependency_overrides[get_shift_repo] = lambda: shift_repo
    app.dependency_overrides[get_application_repo] = lambda: application_repo
    app.dependency_overrides[get_booking_repo] = lambda: booking_repo
    app.dependency_overrides[get_application_decision_repo] = lambda: decision_repo
    yield
    app.dependency_overrides.clear()


@pytest.fixture(autouse=True)
def override_repos(repos):
    yield


def test_create_shift_with_default_workers_needed():
    response = create_shift()

    assert response.status_code == 200
    data = response.json()
    assert data["workers_needed"] == 1
    assert data["workers_filled"] == 0
    assert data["status"] == "open"


def test_create_shift_with_multiple_workers_needed():
    response = create_shift(role="bartender", workers_needed=5, pay_rate=30.0)

    assert response.status_code == 200
    data = response.json()
    assert data["workers_needed"] == 5
    assert data["workers_filled"] == 0
    assert data["status"] == "open"


def test_approve_application_increments_workers_filled():
    shift_id = create_shift(workers_needed=3).json()["shift_id"]
    application_id = apply_to_shift(shift_id, "worker-1").json()["application_id"]

    approve_response = approve_application(application_id)

    assert approve_response.status_code == 200
    shift = get_shift(shift_id)
    assert shift["workers_filled"] == 1
    assert shift["status"] == "open"


def test_shift_status_changes_to_filled_when_capacity_reached():
    shift_id = create_shift(workers_needed=2).json()["shift_id"]
    approve_application(apply_to_shift(shift_id, "worker-1").json()["application_id"])

    shift = get_shift(shift_id)
    assert shift["workers_filled"] == 1
    assert shift["status"] == "open"

    approve_application(apply_to_shift(shift_id, "worker-2").json()["application_id"])

    shift = get_shift(shift_id)
    assert shift["workers_filled"] == 2
    assert shift["status"] == "filled"


def test_cannot_approve_application_when_shift_fully_staffed():
    shift_id = create_shift(workers_needed=1).json()["shift_id"]
    first_application = apply_to_shift(shift_id, "worker-1").json()["application_id"]
    second_application = apply_to_shift(shift_id, "worker-2").json()["application_id"]

    approve1 = approve_application(first_application)
    approve2 = approve_application(second_application)

    assert approve1.status_code == 200
    assert approve2.status_code == 400
    assert "fully staffed" in approve2.json()["detail"].lower()


def test_cannot_apply_to_fully_staffed_shift():
    shift_id = create_shift(workers_needed=1).json()["shift_id"]
    first_application = apply_to_shift(shift_id, "worker-1").json()["application_id"]
    approve_application(first_application)

    response = apply_to_shift(shift_id, "worker-2")

    assert response.status_code == 400
    assert_fully_staffed_or_closed(response.json()["detail"])


def test_multiple_workers_for_large_shift():
    shift_id = create_shift(
        role="event staff",
        location="convention center",
        hours=12,
        pay_rate=20.0,
        workers_needed=5,
    ).json()["shift_id"]

    for worker_number in range(1, 6):
        application_id = apply_to_shift(
            shift_id,
            f"worker-{worker_number}",
        ).json()["application_id"]
        assert approve_application(application_id).status_code == 200

    shift = get_shift(shift_id)
    assert shift["workers_filled"] == 5
    assert shift["workers_needed"] == 5
    assert shift["status"] == "filled"

    extra_app = apply_to_shift(shift_id, "worker-6")
    assert extra_app.status_code == 400
    assert_fully_staffed_or_closed(extra_app.json()["detail"])


def create_shift(
    role: str = "server",
    location: str = "downtown",
    hours: int = 8,
    pay_rate: float = 25.0,
    workers_needed: int | None = None,
):
    now = datetime.utcnow()
    payload = {
        "operator_id": "op-123",
        "role": role,
        "location": location,
        "start_time": (now + timedelta(days=1)).isoformat(),
        "end_time": (now + timedelta(days=1, hours=hours)).isoformat(),
        "pay_rate": pay_rate,
    }
    if workers_needed is not None:
        payload["workers_needed"] = workers_needed
    return client.post("/shifts", json=payload, headers=OPERATOR_HEADERS)


def apply_to_shift(shift_id: str, worker_id: str):
    return client.post(
        "/applications",
        json={"shift_id": shift_id, "worker_id": worker_id},
        headers={"X-Actor-Role": "worker", "X-Actor-Id": worker_id},
    )


def approve_application(application_id: str):
    return client.post(
        f"/applications/{application_id}/approve",
        json={},
        headers=OPERATOR_HEADERS,
    )


def get_shift(shift_id: str) -> dict:
    shifts_response = client.get("/shifts", headers=OPERATOR_HEADERS)
    return next(shift for shift in shifts_response.json() if shift["shift_id"] == shift_id)


def assert_fully_staffed_or_closed(detail: str) -> None:
    lowered = detail.lower()
    assert "fully staffed" in lowered or "not accepting applications" in lowered

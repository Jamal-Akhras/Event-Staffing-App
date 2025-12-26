"""Tests for workers_needed functionality in shifts and bookings."""

from datetime import datetime, timedelta
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from apps.api.src.main import app
from apps.api.src.deps import get_shift_repo, get_application_repo, get_booking_repo
from apps.api.src.repositories.in_memory_shift_repository import InMemoryShiftRepository
from apps.api.src.repositories.in_memory_application_repository import InMemoryApplicationRepository
from apps.api.src.repositories.in_memory_booking_repository import InMemoryBookingRepository

client = TestClient(app)


@pytest.fixture
def shift_repo():
    """Provide a fresh in-memory shift repository for each test."""
    repo = InMemoryShiftRepository()
    yield repo
    repo.clear()


@pytest.fixture
def application_repo():
    """Provide a fresh in-memory application repository for each test."""
    repo = InMemoryApplicationRepository()
    yield repo
    repo.clear()


@pytest.fixture
def booking_repo():
    """Provide a fresh in-memory booking repository for each test."""
    repo = InMemoryBookingRepository()
    yield repo
    repo.clear()


@pytest.fixture(autouse=True)
def override_repos(shift_repo, application_repo, booking_repo):
    """Override repository dependencies for all tests."""
    app.dependency_overrides[get_shift_repo] = lambda: iter([shift_repo])
    app.dependency_overrides[get_application_repo] = lambda: iter([application_repo])
    app.dependency_overrides[get_booking_repo] = lambda: iter([booking_repo])
    yield
    app.dependency_overrides.clear()


def test_create_shift_with_default_workers_needed(shift_repo):
    """Test creating a shift with default workers_needed=1."""
    now = datetime.utcnow()
    response = client.post(
        "/shifts",
        json={
            "operator_id": "op-123",
            "role": "server",
            "location": "downtown",
            "start_time": (now + timedelta(days=1)).isoformat(),
            "end_time": (now + timedelta(days=1, hours=8)).isoformat(),
            "pay_rate": 25.0,
        },
        headers={"X-Actor-Role": "operator"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["workers_needed"] == 1
    assert data["workers_filled"] == 0
    assert data["status"] == "open"


def test_create_shift_with_multiple_workers_needed(shift_repo):
    """Test creating a shift with multiple workers needed."""
    now = datetime.utcnow()
    response = client.post(
        "/shifts",
        json={
            "operator_id": "op-123",
            "role": "bartender",
            "location": "downtown",
            "start_time": (now + timedelta(days=1)).isoformat(),
            "end_time": (now + timedelta(days=1, hours=8)).isoformat(),
            "pay_rate": 30.0,
            "workers_needed": 5,
        },
        headers={"X-Actor-Role": "operator"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["workers_needed"] == 5
    assert data["workers_filled"] == 0
    assert data["status"] == "open"


def test_approve_application_increments_workers_filled():
    """Test that approving an application increments workers_filled."""
    now = datetime.utcnow()

    # Create a shift with workers_needed=3
    shift_response = client.post(
        "/shifts",
        json={
            "operator_id": "op-123",
            "role": "server",
            "location": "downtown",
            "start_time": (now + timedelta(days=1)).isoformat(),
            "end_time": (now + timedelta(days=1, hours=8)).isoformat(),
            "pay_rate": 25.0,
            "workers_needed": 3,
        },
        headers={"X-Actor-Role": "operator"},
    )
    shift_id = shift_response.json()["shift_id"]

    # Create an application
    app_response = client.post(
        "/applications",
        json={
            "shift_id": shift_id,
            "worker_id": "worker-1",
        },
        headers={"X-Actor-Role": "worker"},
    )
    application_id = app_response.json()["application_id"]

    # Approve the application
    approve_response = client.post(
        f"/applications/{application_id}/approve",
        json={},
        headers={"X-Actor-Role": "operator"},
    )
    assert approve_response.status_code == 200

    # Check that workers_filled is now 1 and status is still "open"
    shifts_response = client.get("/shifts", headers={"X-Actor-Role": "operator"})
    shifts = shifts_response.json()
    shift = next(s for s in shifts if s["shift_id"] == shift_id)
    assert shift["workers_filled"] == 1
    assert shift["status"] == "open"


def test_shift_status_changes_to_filled_when_capacity_reached():
    """Test that shift status changes to 'filled' when workers_filled reaches workers_needed."""
    now = datetime.utcnow()

    # Create a shift with workers_needed=2
    shift_response = client.post(
        "/shifts",
        json={
            "operator_id": "op-123",
            "role": "server",
            "location": "downtown",
            "start_time": (now + timedelta(days=1)).isoformat(),
            "end_time": (now + timedelta(days=1, hours=8)).isoformat(),
            "pay_rate": 25.0,
            "workers_needed": 2,
        },
        headers={"X-Actor-Role": "operator"},
    )
    shift_id = shift_response.json()["shift_id"]

    # Create and approve first application
    app1_response = client.post(
        "/applications",
        json={"shift_id": shift_id, "worker_id": "worker-1"},
        headers={"X-Actor-Role": "worker"},
    )
    client.post(
        f"/applications/{app1_response.json()['application_id']}/approve",
        json={},
        headers={"X-Actor-Role": "operator"},
    )

    # Verify status is still "open"
    shifts_response = client.get("/shifts", headers={"X-Actor-Role": "operator"})
    shift = next(s for s in shifts_response.json() if s["shift_id"] == shift_id)
    assert shift["workers_filled"] == 1
    assert shift["status"] == "open"

    # Create and approve second application
    app2_response = client.post(
        "/applications",
        json={"shift_id": shift_id, "worker_id": "worker-2"},
        headers={"X-Actor-Role": "worker"},
    )
    client.post(
        f"/applications/{app2_response.json()['application_id']}/approve",
        json={},
        headers={"X-Actor-Role": "operator"},
    )

    # Verify status is now "filled"
    shifts_response = client.get("/shifts", headers={"X-Actor-Role": "operator"})
    shift = next(s for s in shifts_response.json() if s["shift_id"] == shift_id)
    assert shift["workers_filled"] == 2
    assert shift["status"] == "filled"


def test_cannot_approve_application_when_shift_fully_staffed():
    """Test that approving an application fails when shift is already fully staffed."""
    now = datetime.utcnow()

    # Create a shift with workers_needed=1
    shift_response = client.post(
        "/shifts",
        json={
            "operator_id": "op-123",
            "role": "server",
            "location": "downtown",
            "start_time": (now + timedelta(days=1)).isoformat(),
            "end_time": (now + timedelta(days=1, hours=8)).isoformat(),
            "pay_rate": 25.0,
            "workers_needed": 1,
        },
        headers={"X-Actor-Role": "operator"},
    )
    shift_id = shift_response.json()["shift_id"]

    # Create two applications
    app1_response = client.post(
        "/applications",
        json={"shift_id": shift_id, "worker_id": "worker-1"},
        headers={"X-Actor-Role": "worker"},
    )
    app2_response = client.post(
        "/applications",
        json={"shift_id": shift_id, "worker_id": "worker-2"},
        headers={"X-Actor-Role": "worker"},
    )

    # Approve first application
    approve1 = client.post(
        f"/applications/{app1_response.json()['application_id']}/approve",
        json={},
        headers={"X-Actor-Role": "operator"},
    )
    assert approve1.status_code == 200

    # Try to approve second application - should fail
    approve2 = client.post(
        f"/applications/{app2_response.json()['application_id']}/approve",
        json={},
        headers={"X-Actor-Role": "operator"},
    )
    assert approve2.status_code == 400
    assert "fully staffed" in approve2.json()["detail"].lower()


def test_cannot_apply_to_fully_staffed_shift():
    """Test that workers cannot apply to a shift that is already fully staffed."""
    now = datetime.utcnow()

    # Create a shift with workers_needed=1
    shift_response = client.post(
        "/shifts",
        json={
            "operator_id": "op-123",
            "role": "server",
            "location": "downtown",
            "start_time": (now + timedelta(days=1)).isoformat(),
            "end_time": (now + timedelta(days=1, hours=8)).isoformat(),
            "pay_rate": 25.0,
            "workers_needed": 1,
        },
        headers={"X-Actor-Role": "operator"},
    )
    shift_id = shift_response.json()["shift_id"]

    # Create and approve first application
    app1_response = client.post(
        "/applications",
        json={"shift_id": shift_id, "worker_id": "worker-1"},
        headers={"X-Actor-Role": "worker"},
    )
    client.post(
        f"/applications/{app1_response.json()['application_id']}/approve",
        json={},
        headers={"X-Actor-Role": "operator"},
    )

    # Try to create another application - should fail
    app2_response = client.post(
        "/applications",
        json={"shift_id": shift_id, "worker_id": "worker-2"},
        headers={"X-Actor-Role": "worker"},
    )
    assert app2_response.status_code == 400
    assert "fully staffed" in app2_response.json()["detail"].lower()


def test_multiple_workers_for_large_shift():
    """Test a shift with many workers needed (5) and verify all positions can be filled."""
    now = datetime.utcnow()

    # Create a shift with workers_needed=5
    shift_response = client.post(
        "/shifts",
        json={
            "operator_id": "op-123",
            "role": "event staff",
            "location": "convention center",
            "start_time": (now + timedelta(days=1)).isoformat(),
            "end_time": (now + timedelta(days=1, hours=12)).isoformat(),
            "pay_rate": 20.0,
            "workers_needed": 5,
        },
        headers={"X-Actor-Role": "operator"},
    )
    shift_id = shift_response.json()["shift_id"]

    # Create and approve 5 applications
    for i in range(5):
        app_response = client.post(
            "/applications",
            json={"shift_id": shift_id, "worker_id": f"worker-{i+1}"},
            headers={"X-Actor-Role": "worker"},
        )
        approve_response = client.post(
            f"/applications/{app_response.json()['application_id']}/approve",
            json={},
            headers={"X-Actor-Role": "operator"},
        )
        assert approve_response.status_code == 200

    # Verify shift is now filled
    shifts_response = client.get("/shifts", headers={"X-Actor-Role": "operator"})
    shift = next(s for s in shifts_response.json() if s["shift_id"] == shift_id)
    assert shift["workers_filled"] == 5
    assert shift["workers_needed"] == 5
    assert shift["status"] == "filled"

    # Try to create one more application - should fail
    extra_app = client.post(
        "/applications",
        json={"shift_id": shift_id, "worker_id": "worker-6"},
        headers={"X-Actor-Role": "worker"},
    )
    assert extra_app.status_code == 400
    assert "fully staffed" in extra_app.json()["detail"].lower()

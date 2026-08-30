from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from apps.api.src import main
from apps.api.src.deps import get_booking_charge_repo, get_booking_repo, get_booking_transition_repo, get_shift_repo
from apps.api.src.models.shift import Shift
from apps.api.src.repositories.in_memory_booking_repository import InMemoryBookingRepository
from apps.api.src.repositories.in_memory_shift_repository import InMemoryShiftRepository
from apps.api.src.repository_dependencies import shared_booking_charge_repository, shared_booking_transition_repository, shared_event_repository
from packages.domain.src.booking import Booking

OPERATOR = {"X-Actor-Role": "operator", "X-Actor-Id": "operator-1", "X-Account-Id": "venue-1"}
OTHER_OPERATOR = {"X-Actor-Role": "operator", "X-Actor-Id": "operator-2", "X-Account-Id": "venue-2"}
WORKER = {"X-Actor-Role": "worker", "X-Actor-Id": "worker-1"}
SYSTEM = {"X-Actor-Role": "system", "X-Actor-Id": "system"}
NOW = datetime(2030, 1, 1, 12, 0, tzinfo=UTC)


@pytest.fixture(autouse=True)
def clear_events():
    shared_event_repository().clear()
    yield
    shared_event_repository().clear()


def _events(client: TestClient, **params) -> list[dict]:
    response = client.get("/system/events", params={"limit": 500, **params}, headers=SYSTEM)
    assert response.status_code == 200
    return response.json()["events"]


def _client_with_booking():
    bookings = InMemoryBookingRepository()
    shifts = InMemoryShiftRepository(bookings)
    bookings.attach_shift_repo(shifts)
    shifts.save(
        Shift(
            shift_id="shift-1",
            operator_id="operator-1",
            account_id="venue-1",
            role="Bartender",
            location="Main bar",
            start_time=NOW + timedelta(minutes=60),
            end_time=NOW + timedelta(minutes=300),
            pay_rate=14,
            notes=None,
            status="filled",
            created_at=NOW,
            workers_needed=1,
            workers_filled=1,
        )
    )
    booking_id = str(uuid4())
    bookings.save(
        Booking(
            booking_id=booking_id,
            shift_id="shift-1",
            worker_id="worker-1",
            operator_id="operator-1",
            start_time=NOW + timedelta(minutes=60),
            end_time=NOW + timedelta(minutes=300),
            created_at=NOW,
        )
    )
    main.app.dependency_overrides[get_booking_repo] = lambda: bookings
    main.app.dependency_overrides[get_booking_transition_repo] = shared_booking_transition_repository
    main.app.dependency_overrides[get_booking_charge_repo] = shared_booking_charge_repository
    main.app.dependency_overrides[get_shift_repo] = lambda: shifts
    return TestClient(main.app), booking_id


def test_every_mutating_request_is_audited_and_reads_are_not():
    client = TestClient(main.app)
    client.post("/auth/login", json={"email": "nobody@example.com", "password": "wrong-password"})
    client.get("/bookings", headers=OPERATOR)

    audit = _events(client, name="http.request")
    assert len(audit) == 1
    assert audit[0]["context"]["method"] == "POST"
    assert audit[0]["subject_id"] == "/auth/login"
    assert audit[0]["status_code"] == 401
    assert audit[0]["duration_ms"] is not None
    assert audit[0]["request_id"]


def test_audit_captures_the_acting_user_and_route_template():
    client, booking_id = _client_with_booking()
    client.post(f"/bookings/{booking_id}/confirm", json={"now": NOW.isoformat()}, headers=OPERATOR)

    audit = _events(client, name="http.request")[0]
    assert audit["actor_user_id"] == "operator-1"
    assert audit["actor_role"] == "operator"
    assert audit["venue_id"] == "venue-1"
    assert audit["subject_id"] == "/bookings/{booking_id}/confirm"
    assert audit["status_code"] == 200


def test_booking_transitions_record_lifecycle_events():
    client, booking_id = _client_with_booking()
    client.post(f"/bookings/{booking_id}/confirm", json={"now": NOW.isoformat()}, headers=OPERATOR)
    booking = main.app.dependency_overrides[get_booking_repo]().get(booking_id)
    client.post(
        f"/bookings/{booking_id}/check-in",
        json={"now": (NOW + timedelta(minutes=40)).isoformat(), "code": booking.check_in_code},
        headers=WORKER,
    )

    assert _events(client, name="booking.confirmed")
    checked_in = _events(client, name="booking.checked_in")[0]
    assert checked_in["category"] == "lifecycle"
    assert checked_in["subject_type"] == "booking"
    assert checked_in["subject_id"] == booking_id
    assert checked_in["worker_id"] == "worker-1"
    assert checked_in["context"]["shift_id"] == "shift-1"


def test_login_outcomes_are_recorded_without_the_password():
    client = TestClient(main.app)
    client.post("/auth/login", json={"email": "nobody@example.com", "password": "hunter2-secret"})

    failures = _events(client, name="auth.login_failed")
    assert len(failures) == 1
    assert failures[0]["category"] == "auth"
    assert failures[0]["context"]["reason"] == "invalid_credentials"
    for event in _events(client):
        assert "hunter2-secret" not in str(event["context"])


def test_clients_can_send_behavioural_events():
    client = TestClient(main.app)
    response = client.post(
        "/events",
        json={
            "events": [
                {"name": "shift.viewed", "subject_type": "shift", "subject_id": "shift-1", "context": {"position": 3}},
                {"name": "feed.searched", "context": {"query": "bartender"}},
            ]
        },
        headers={**WORKER, "X-Client": "mobile", "X-Session-Id": "session-abc", "X-App-Version": "1.4.0"},
    )
    assert response.status_code == 202
    assert response.json() == {"recorded": 2}

    viewed = _events(client, name="shift.viewed")[0]
    assert viewed["category"] == "behaviour"
    assert viewed["source"] == "mobile"
    assert viewed["session_id"] == "session-abc"
    assert viewed["app_version"] == "1.4.0"
    assert viewed["worker_id"] == "worker-1"
    assert viewed["context"]["position"] == 3


def test_ingest_rejects_bad_names_and_oversized_batches():
    client = TestClient(main.app)
    assert client.post("/events", json={"events": [{"name": "Not A Name"}]}, headers=WORKER).status_code == 422
    assert client.post("/events", json={"events": []}, headers=WORKER).status_code == 422
    too_many = {"events": [{"name": "shift.viewed"} for _ in range(51)]}
    assert client.post("/events", json=too_many, headers=WORKER).status_code == 422


def test_secrets_in_client_context_are_redacted():
    client = TestClient(main.app)
    client.post(
        "/events",
        json={"events": [{"name": "form.submitted", "context": {"password": "leak-me", "field": "email"}}]},
        headers=WORKER,
    )
    event = _events(client, name="form.submitted")[0]
    assert event["context"]["password"] == "[redacted]"
    assert event["context"]["field"] == "email"


def test_activity_is_scoped_and_system_query_requires_the_system_role():
    client, booking_id = _client_with_booking()
    client.post(f"/bookings/{booking_id}/confirm", json={"now": NOW.isoformat()}, headers=OPERATOR)

    mine = client.get("/activity", headers=OPERATOR).json()["events"]
    assert mine and all(event["venue_id"] == "venue-1" for event in mine)
    assert client.get("/activity", headers=OTHER_OPERATOR).json()["events"] == []

    assert client.get("/system/events", headers=OPERATOR).status_code == 403
    assert len(_events(client)) >= len(mine)
    counts = client.get("/system/events/counts", headers=SYSTEM).json()["counts"]
    assert counts["booking.confirmed"] == 1


def test_the_event_log_cannot_be_edited_over_the_api():
    client = TestClient(main.app)
    assert client.put("/events", json={}, headers=SYSTEM).status_code == 405
    assert client.delete("/events", headers=SYSTEM).status_code == 405

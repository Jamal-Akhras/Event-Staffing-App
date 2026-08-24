from __future__ import annotations

from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient

from apps.api.src import main
from apps.api.src.deps import (
    get_application_decision_repo,
    get_application_repo,
    get_booking_repo,
    get_notification_repo,
    get_outbox_publisher,
    get_shift_repo,
)
from apps.api.src.repositories.in_memory_application_decision_repository import (
    InMemoryApplicationDecisionRepository,
)
from apps.api.src.repositories.in_memory_application_repository import InMemoryApplicationRepository
from apps.api.src.repositories.in_memory_booking_repository import InMemoryBookingRepository
from apps.api.src.repositories.in_memory_notification_repository import InMemoryNotificationRepository
from apps.api.src.repositories.in_memory_shift_repository import InMemoryShiftRepository
from apps.api.src.services.email import LoggingEmailTransport
from apps.api.src.services.outbox_publisher import InMemoryOutboxPublisher
from packages.domain.src.booking_state import BookingState

NOW = datetime(2030, 1, 1, 9, 0, tzinfo=UTC)
OPERATOR = {"X-Actor-Role": "operator", "X-Actor-Id": "operator-1"}
OTHER_OPERATOR = {"X-Actor-Role": "operator", "X-Actor-Id": "operator-2"}
WORKER = {"X-Actor-Role": "worker", "X-Actor-Id": "worker-1"}
SECOND_WORKER = {"X-Actor-Role": "worker", "X-Actor-Id": "worker-2"}


def _client():
    applications = InMemoryApplicationRepository()
    bookings = InMemoryBookingRepository()
    shifts = InMemoryShiftRepository(bookings)
    notifications = InMemoryNotificationRepository()
    applications.attach_shift_repo(shifts)
    bookings.attach_shift_repo(shifts)
    decisions = InMemoryApplicationDecisionRepository(applications, bookings, shifts)
    main.app.dependency_overrides[get_application_repo] = lambda: applications
    main.app.dependency_overrides[get_booking_repo] = lambda: bookings
    main.app.dependency_overrides[get_shift_repo] = lambda: shifts
    main.app.dependency_overrides[get_notification_repo] = lambda: notifications
    publisher = InMemoryOutboxPublisher(notifications, LoggingEmailTransport())
    main.app.dependency_overrides[get_outbox_publisher] = lambda: publisher
    main.app.dependency_overrides[get_application_decision_repo] = lambda: decisions
    return TestClient(main.app), applications, bookings, shifts, notifications


def _create_shift(client: TestClient, workers_needed: int = 1) -> dict:
    response = client.post(
        "/shifts",
        json={
            "role": "Bartender",
            "location": "Main bar",
            "start_time": (NOW + timedelta(hours=4)).isoformat(),
            "end_time": (NOW + timedelta(hours=9)).isoformat(),
            "pay_rate": 15,
            "workers_needed": workers_needed,
            "notes": "Black shirt",
            "now": NOW.isoformat(),
        },
        headers=OPERATOR,
    )
    assert response.status_code == 200, response.text
    return response.json()


def _apply(client: TestClient, shift_id: str, worker_headers=WORKER) -> dict:
    worker_id = worker_headers["X-Actor-Id"]
    response = client.post(
        "/applications",
        json={
            "shift_id": shift_id,
            "worker_id": worker_id,
            "message": "Available",
            "now": (NOW + timedelta(minutes=10)).isoformat(),
        },
        headers=worker_headers,
    )
    assert response.status_code == 200, response.text
    return response.json()


def _approve(client: TestClient, application_id: str) -> dict:
    response = client.post(
        f"/applications/{application_id}/approve",
        json={"now": (NOW + timedelta(minutes=20)).isoformat()},
        headers=OPERATOR,
    )
    assert response.status_code == 200, response.text
    return response.json()


def test_worker_can_withdraw_only_their_pending_application():
    client, applications, _, _, _ = _client()
    shift = _create_shift(client)
    application = _apply(client, shift["shift_id"])

    forbidden = client.post(
        f"/applications/{application['application_id']}/withdraw",
        json={"reason": "Plans changed", "now": (NOW + timedelta(minutes=30)).isoformat()},
        headers=SECOND_WORKER,
    )
    assert forbidden.status_code == 403

    response = client.post(
        f"/applications/{application['application_id']}/withdraw",
        json={"reason": "Plans changed", "now": (NOW + timedelta(minutes=30)).isoformat()},
        headers=WORKER,
    )
    assert response.status_code == 200, response.text
    assert response.json()["status"] == "withdrawn"
    stored = applications.get(application["application_id"])
    assert stored.withdrawal_reason == "Plans changed"
    assert stored.withdrawn_at == NOW + timedelta(minutes=30)


def test_closing_shift_rejects_pending_applications_but_preserves_bookings():
    client, applications, bookings, _, notifications = _client()
    shift = _create_shift(client, workers_needed=2)
    approved = _approve(client, _apply(client, shift["shift_id"])["application_id"])
    pending = _apply(client, shift["shift_id"], SECOND_WORKER)

    response = client.post(
        f"/shifts/{shift['shift_id']}/close",
        json={"now": (NOW + timedelta(hours=1)).isoformat()},
        headers=OPERATOR,
    )
    assert response.status_code == 200, response.text
    assert response.json()["status"] == "closed"
    assert applications.get(pending["application_id"]).status == "rejected"
    assert bookings.get(approved["booking_id"]).state == BookingState.CONFIRMED
    assert notifications.list_for_worker("worker-2")[0].type == "shift_unavailable"


def test_shift_edit_locks_contract_terms_after_booking_but_allows_notes_and_capacity():
    client, _, _, _, _ = _client()
    shift = _create_shift(client)
    _approve(client, _apply(client, shift["shift_id"])["application_id"])
    payload = {
        "role": shift["role"],
        "location": shift["location"],
        "start_time": shift["start_time"],
        "end_time": shift["end_time"],
        "pay_rate": shift["pay_rate"],
        "workers_needed": 2,
        "notes": "Use the side entrance",
        "now": (NOW + timedelta(hours=1)).isoformat(),
    }
    allowed = client.put(f"/shifts/{shift['shift_id']}", json=payload, headers=OPERATOR)
    assert allowed.status_code == 200, allowed.text
    assert allowed.json()["workers_needed"] == 2
    assert allowed.json()["notes"] == "Use the side entrance"

    payload["pay_rate"] = 16
    locked = client.put(f"/shifts/{shift['shift_id']}", json=payload, headers=OPERATOR)
    assert locked.status_code == 400


def test_cancelling_shift_is_atomic_and_audited():
    client, applications, bookings, shifts, notifications = _client()
    shift = _create_shift(client, workers_needed=2)
    approved = _approve(client, _apply(client, shift["shift_id"])["application_id"])
    pending = _apply(client, shift["shift_id"], SECOND_WORKER)

    forbidden = client.post(
        f"/shifts/{shift['shift_id']}/cancel",
        json={"reason": "Venue closure", "now": (NOW + timedelta(hours=1)).isoformat()},
        headers=OTHER_OPERATOR,
    )
    assert forbidden.status_code == 403

    response = client.post(
        f"/shifts/{shift['shift_id']}/cancel",
        json={"reason": "Venue closure", "now": (NOW + timedelta(hours=1)).isoformat()},
        headers=OPERATOR,
    )
    assert response.status_code == 200, response.text
    assert response.json()["status"] == "cancelled"
    assert shifts.get(shift["shift_id"]).workers_filled == 0
    booking = bookings.get(approved["booking_id"])
    assert booking.state == BookingState.CANCELLED_BY_OPERATOR
    assert booking.cancellation_reason == "Venue closure"
    assert applications.get(pending["application_id"]).status == "rejected"
    assert notifications.list_for_worker("worker-1")[0].type == "shift_cancelled"


def test_worker_booking_cancellation_requires_reason_and_records_actor():
    client, _, bookings, shifts, _ = _client()
    shift = _create_shift(client)
    approved = _approve(client, _apply(client, shift["shift_id"])["application_id"])

    missing_reason = client.post(
        f"/bookings/{approved['booking_id']}/cancel/worker",
        json={"now": (NOW + timedelta(hours=1)).isoformat()},
        headers=WORKER,
    )
    assert missing_reason.status_code == 422

    response = client.post(
        f"/bookings/{approved['booking_id']}/cancel/worker",
        json={"reason": "Illness", "now": (NOW + timedelta(hours=1)).isoformat()},
        headers=WORKER,
    )
    assert response.status_code == 200, response.text
    booking = bookings.get(approved["booking_id"])
    assert booking.cancellation_reason == "Illness"
    assert booking.cancelled_by_user_id == "worker-1"
    assert shifts.get(shift["shift_id"]).status == "open"

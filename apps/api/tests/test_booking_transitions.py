from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from apps.api.src import main
from apps.api.src.deps import get_booking_charge_repo, get_booking_repo, get_booking_transition_repo, get_shift_repo
from apps.api.src.models.shift import Shift
from apps.api.src.repositories.in_memory_booking_repository import InMemoryBookingRepository
from apps.api.src.repositories.in_memory_shift_repository import InMemoryShiftRepository
from apps.api.src.repository_dependencies import shared_booking_charge_repository, shared_booking_transition_repository
from packages.domain.src.booking import Booking

OPERATOR = {"X-Actor-Role": "operator", "X-Actor-Id": "operator-1", "X-Account-Id": "venue-1"}
WORKER = {"X-Actor-Role": "worker", "X-Actor-Id": "worker-1"}
OTHER_VENUE = {"X-Actor-Role": "operator", "X-Actor-Id": "operator-2", "X-Account-Id": "venue-2"}
NOW = datetime(2030, 1, 1, 12, 0, tzinfo=UTC)


@pytest.fixture(autouse=True)
def clear_transitions():
    shared_booking_transition_repository().clear()
    yield
    shared_booking_transition_repository().clear()


def _client():
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


def test_each_state_change_records_who_made_it():
    client, booking_id = _client()
    client.post(f"/bookings/{booking_id}/confirm", json={"now": NOW.isoformat()}, headers=OPERATOR)
    booking = main.app.dependency_overrides[get_booking_repo]().get(booking_id)
    client.post(
        f"/bookings/{booking_id}/check-in",
        json={"now": (NOW + timedelta(minutes=40)).isoformat(), "code": booking.check_in_code},
        headers=WORKER,
    )

    history = client.get(f"/bookings/{booking_id}/transitions", headers=OPERATOR).json()
    assert [(item["from_state"], item["to_state"]) for item in history] == [
        ("requested", "confirmed"),
        ("confirmed", "checked_in"),
    ]
    assert history[0]["actor_user_id"] == "operator-1"
    assert history[0]["actor_role"] == "operator"
    assert history[1]["actor_user_id"] == "worker-1"
    assert history[1]["actor_role"] == "worker"


def test_a_cancellation_records_its_reason_and_who_gave_it():
    client, booking_id = _client()
    client.post(f"/bookings/{booking_id}/confirm", json={"now": NOW.isoformat()}, headers=OPERATOR)
    cancelled = client.post(
        f"/bookings/{booking_id}/cancel/operator",
        json={"reason": "Event was called off", "reason_code": "venue_event_cancelled", "now": NOW.isoformat()},
        headers=OPERATOR,
    )
    assert cancelled.status_code == 200

    history = client.get(f"/bookings/{booking_id}/transitions", headers=OPERATOR).json()
    last = history[-1]
    assert last["to_state"] == "cancelled_by_operator"
    assert last["reason_code"] == "venue_event_cancelled"
    assert last["reason_note"] == "Event was called off"
    assert last["actor_role"] == "operator"


def test_an_unknown_reason_code_is_rejected():
    client, booking_id = _client()
    client.post(f"/bookings/{booking_id}/confirm", json={"now": NOW.isoformat()}, headers=OPERATOR)
    response = client.post(
        f"/bookings/{booking_id}/cancel/operator",
        json={"reason": "made up", "reason_code": "because_i_said_so", "now": NOW.isoformat()},
        headers=OPERATOR,
    )
    assert response.status_code == 422


def test_history_is_venue_scoped():
    client, booking_id = _client()
    client.post(f"/bookings/{booking_id}/confirm", json={"now": NOW.isoformat()}, headers=OPERATOR)
    assert client.get(f"/bookings/{booking_id}/transitions", headers=OTHER_VENUE).status_code == 403
    assert client.get(f"/bookings/{booking_id}/transitions", headers=WORKER).status_code == 200

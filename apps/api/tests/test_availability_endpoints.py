from dataclasses import replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal

from fastapi.testclient import TestClient

from apps.api.src import main
from apps.api.src.models.account import Account
from apps.api.src.models.availability import TimeOffStatus
from apps.api.src.models.event import EventQuery
from apps.api.src.models.shift import Shift
from apps.api.src.models.worker_profile import WorkerProfile
from apps.api.src.models.worker_relationship import WorkerRelationship
from apps.api.src.repository_dependencies import (
    get_account_repo,
    get_booking_repo,
    get_event_repo,
    get_shift_repo,
    get_worker_profile_repo,
)
from apps.api.src.repository_dependencies_workforce import get_worker_relationship_repo
from apps.api.src.deps import get_idempotency_service
from apps.api.src.services.idempotency import IdempotencyService
from packages.domain.src.booking import Booking
from packages.domain.src.booking_state import BookingState

NOW = datetime(2030, 6, 1, 9, tzinfo=UTC)
WORKER = {"X-Actor-Role": "worker", "X-Actor-Id": "worker-1"}
OPERATOR = {"X-Actor-Role": "operator", "X-Actor-Id": "manager-1", "X-Account-Id": "venue-1"}
OTHER_OPERATOR = {
    "X-Actor-Role": "operator",
    "X-Actor-Id": "manager-2",
    "X-Account-Id": "venue-2",
}


def _client(in_memory_repos) -> TestClient:
    main.app.dependency_overrides[get_idempotency_service] = lambda: IdempotencyService(None)
    for venue_id in ("venue-1", "venue-2"):
        in_memory_repos[get_account_repo].save(
            Account(
                account_id=venue_id,
                name=f"Venue {venue_id}",
                country="GB",
                currency="GBP",
                created_at=NOW,
            )
        )
    in_memory_repos[get_worker_profile_repo].save(
        WorkerProfile(
            worker_id="worker-1",
            display_name="Alex Worker",
            role="Bartender",
            city="Bath",
            experience_years=3,
            reliability_score=1,
            badges=[],
            bio=None,
            languages=["English"],
            email="alex@example.com",
            phone=None,
            address=None,
            emergency_contact=None,
            pay_rate=None,
            notes=None,
            updated_at=NOW,
        )
    )
    in_memory_repos[get_worker_relationship_repo].save(
        WorkerRelationship(
            relationship_id="relationship-1",
            venue_id="venue-1",
            worker_id="worker-1",
            relationship_type="permanent",
            status="active",
            created_at=NOW,
            updated_at=NOW,
        )
    )
    return TestClient(main.app)


def test_rules_and_exceptions_are_idempotent_and_audited(in_memory_repos):
    client = _client(in_memory_repos)
    rules_payload = {
        "rules": [
            {
                "timezone": "Europe/London",
                "weekday": 1,
                "start_minute": 540,
                "duration_minutes": 480,
                "effective_from": "2030-06-01",
            }
        ]
    }
    first = client.put(
        "/me/availability/rules",
        json=rules_payload,
        headers={**WORKER, "Idempotency-Key": "rules-1"},
    )
    replay = client.put(
        "/me/availability/rules",
        json=rules_payload,
        headers={**WORKER, "Idempotency-Key": "rules-1"},
    )

    assert first.status_code == 200
    assert replay.json() == first.json()
    assert replay.headers["Idempotency-Replayed"] == "true"
    assert client.get("/me/availability/rules", headers=WORKER).json() == first.json()

    exception = client.post(
        "/me/availability/exceptions",
        json={
            "kind": "unavailable",
            "start_time": "2030-06-10T09:00:00Z",
            "end_time": "2030-06-10T12:00:00Z",
            "note": "Appointment",
        },
        headers={**WORKER, "Idempotency-Key": "exception-1"},
    )
    assert exception.status_code == 201
    exception_id = exception.json()["exception_id"]
    deleted = client.delete(
        f"/me/availability/exceptions/{exception_id}",
        headers={**WORKER, "Idempotency-Key": "exception-delete-1"},
    )
    assert deleted.status_code == 200
    assert client.get("/me/availability/exceptions", headers=WORKER).json() == []

    events = in_memory_repos[get_event_repo].query(EventQuery(worker_id="worker-1", limit=20))
    names = {event.name for event in events}
    assert {
        "availability.rules_replaced",
        "availability.exception_created",
        "availability.exception_deleted",
    }.issubset(names)


def test_time_off_requires_employment_and_is_venue_scoped(in_memory_repos):
    client = _client(in_memory_repos)
    payload = {
        "venue_id": "venue-1",
        "start_time": "2030-06-10T09:00:00Z",
        "end_time": "2030-06-12T18:00:00Z",
        "reason": "Holiday",
    }
    created = client.post(
        "/me/time-off",
        json=payload,
        headers={**WORKER, "Idempotency-Key": "time-off-1"},
    )
    assert created.status_code == 201, created.text
    request_id = created.json()["request_id"]
    assert client.get("/venues/me/time-off?status=pending", headers=OPERATOR).json()[0][
        "request_id"
    ] == request_id
    assert client.get("/venues/me/time-off", headers=OTHER_OPERATOR).json() == []
    foreign = client.post(
        f"/venues/me/time-off/{request_id}/decline",
        headers={**OTHER_OPERATOR, "Idempotency-Key": "foreign-decline"},
    )
    assert foreign.status_code == 404

    withdrawn = client.post(
        f"/me/time-off/{request_id}/withdraw",
        headers={**WORKER, "Idempotency-Key": "withdraw-1"},
    )
    assert withdrawn.status_code == 200
    assert withdrawn.json()["status"] == "withdrawn"

    second = client.post(
        "/me/time-off",
        json={**payload, "start_time": "2030-06-20T09:00:00Z", "end_time": "2030-06-21T18:00:00Z"},
        headers={**WORKER, "Idempotency-Key": "time-off-2"},
    )
    declined = client.post(
        f"/venues/me/time-off/{second.json()['request_id']}/decline",
        headers={**OPERATOR, "Idempotency-Key": "decline-2"},
    )
    assert declined.status_code == 200
    assert declined.json()["status"] == "declined"

    events = in_memory_repos[get_event_repo].query(EventQuery(venue_id="venue-1", limit=20))
    names = {event.name for event in events}
    assert {"time_off.requested", "time_off.withdrawn", "time_off.declined"}.issubset(names)

    relationship = in_memory_repos[get_worker_relationship_repo].get("relationship-1")
    in_memory_repos[get_worker_relationship_repo].save(replace(relationship, status="ended"))
    refused = client.post(
        "/me/time-off",
        json=payload,
        headers={**WORKER, "Idempotency-Key": "time-off-refused"},
    )
    assert refused.status_code == 400


def test_approval_reports_every_conflicting_venue_booking(in_memory_repos):
    client = _client(in_memory_repos)
    created = client.post(
        "/me/time-off",
        json={
            "venue_id": "venue-1",
            "start_time": "2030-06-10T09:00:00Z",
            "end_time": "2030-06-12T18:00:00Z",
            "reason": "Holiday",
        },
        headers={**WORKER, "Idempotency-Key": "approval-request"},
    ).json()
    shifts = in_memory_repos[get_shift_repo]
    bookings = in_memory_repos[get_booking_repo]
    for index, venue_id in enumerate(("venue-1", "venue-1", "venue-2"), start=1):
        start_time = datetime(2030, 6, 10 + index - 1, 12, tzinfo=UTC)
        shift_id = f"shift-{index}"
        shifts.save(_shift(shift_id, venue_id, start_time))
        bookings.save(
            Booking(
                booking_id=f"booking-{index}",
                shift_id=shift_id,
                worker_id="worker-1",
                operator_id=f"manager-{index}",
                start_time=start_time,
                end_time=start_time + timedelta(hours=4),
                state=BookingState.CONFIRMED,
                created_at=NOW,
            )
        )

    conflict = client.post(
        f"/venues/me/time-off/{created['request_id']}/approve",
        headers={**OPERATOR, "Idempotency-Key": "approve-1"},
    )
    assert conflict.status_code == 409
    assert "booking-1" in conflict.text and "booking-2" in conflict.text
    assert "booking-3" not in conflict.text

    for booking_id in ("booking-1", "booking-2"):
        bookings.save(replace(bookings.get(booking_id), state=BookingState.CANCELLED_BY_OPERATOR))
    approved = client.post(
        f"/venues/me/time-off/{created['request_id']}/approve",
        headers={**OPERATOR, "Idempotency-Key": "approve-1"},
    )
    assert approved.status_code == 200, approved.text
    assert approved.json()["status"] == TimeOffStatus.APPROVED.value
    assert approved.json()["decided_by_user_id"] == "manager-1"

    events = in_memory_repos[get_event_repo].query(EventQuery(venue_id="venue-1", limit=20))
    approval_event = next(event for event in events if event.name == "time_off.approved")
    assert approval_event.worker_id == "worker-1"


def _shift(shift_id: str, venue_id: str, start_time: datetime) -> Shift:
    return Shift(
        shift_id=shift_id,
        operator_id="manager-1",
        account_id=venue_id,
        role="Bartender",
        location="Main bar",
        start_time=start_time,
        end_time=start_time + timedelta(hours=4),
        pay_rate=Decimal("15"),
        notes=None,
        status="filled",
        created_at=NOW,
        workers_needed=1,
        workers_filled=1,
    )

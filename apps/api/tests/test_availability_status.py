from __future__ import annotations

from datetime import UTC, datetime, timedelta

from apps.api.src.models.availability import (
    AvailabilityException,
    AvailabilityExceptionKind,
    TimeOffRequest,
    TimeOffStatus,
    WorkerAvailabilityStatus,
)
from apps.api.src.services.availability_gate import (
    ApprovedTimeOffConflictError,
    AvailabilityGate,
)
from apps.api.src.services.availability_service import AvailabilityService
from packages.domain.src.booking import Booking
from packages.domain.src.booking_state import BookingState

NOW = datetime(2026, 2, 2, 12, tzinfo=UTC)


class RuleRepository:
    def list_for_worker(self, worker_id):
        return []

    def list_for_workers(self, worker_ids):
        return []


class ExceptionRepository:
    def __init__(self, exceptions):
        self.exceptions = exceptions

    def list_overlapping_workers(self, worker_ids, start_time, end_time):
        return [
            item
            for item in self.exceptions
            if item.worker_id in worker_ids
            and item.start_time < end_time
            and item.end_time > start_time
        ]


class TimeOffRepository:
    def __init__(self, requests):
        self.requests = requests
        self.last_query = None

    def list_overlapping_workers(
        self, worker_ids, start_time, end_time, venue_id=None, statuses=None
    ):
        self.last_query = (worker_ids, start_time, end_time, venue_id, statuses)
        return [
            item
            for item in self.requests
            if item.worker_id in worker_ids
            and (venue_id is None or item.venue_id == venue_id)
            and (statuses is None or item.status in statuses)
            and item.start_time < end_time
            and item.end_time > start_time
        ]


class BookingRepository:
    def __init__(self, bookings):
        self.bookings = bookings
        self.calls = 0

    def list_live_for_workers(self, worker_ids, at):
        self.calls += 1
        return [booking for booking in self.bookings if booking.worker_id in worker_ids]


def _time_off(request_id, worker_id, venue_id="venue-1"):
    return TimeOffRequest(
        request_id=request_id,
        worker_id=worker_id,
        venue_id=venue_id,
        start_time=NOW - timedelta(hours=1),
        end_time=NOW + timedelta(hours=1),
        status=TimeOffStatus.APPROVED,
        reason="Holiday",
        created_at=NOW - timedelta(days=1),
        updated_at=NOW,
        decided_at=NOW,
        decided_by_user_id="manager-1",
    )


def test_current_status_priority_is_batched_and_venue_scoped():
    bookings = BookingRepository(
        [
            Booking(
                booking_id="booking-1",
                shift_id="shift-1",
                worker_id="booked",
                operator_id="operator-1",
                start_time=NOW - timedelta(hours=1),
                end_time=NOW + timedelta(hours=1),
                state=BookingState.CONFIRMED,
            )
        ]
    )
    exceptions = ExceptionRepository(
        [
            AvailabilityException(
                exception_id="exception-1",
                worker_id="unavailable",
                kind=AvailabilityExceptionKind.UNAVAILABLE,
                start_time=NOW - timedelta(hours=1),
                end_time=NOW + timedelta(hours=1),
                created_at=NOW,
                updated_at=NOW,
            )
        ]
    )
    time_off = TimeOffRepository(
        [_time_off("away-1", "away"), _time_off("private-1", "other-venue", "venue-2")]
    )
    service = AvailabilityService(RuleRepository(), exceptions, time_off, bookings)

    statuses = service.current_statuses(
        "venue-1", ["booked", "away", "unavailable", "other-venue", "available"], NOW
    )

    assert {worker: result.status for worker, result in statuses.items()} == {
        "booked": WorkerAvailabilityStatus.BOOKED,
        "away": WorkerAvailabilityStatus.AWAY,
        "unavailable": WorkerAvailabilityStatus.UNAVAILABLE,
        "other-venue": WorkerAvailabilityStatus.AVAILABLE,
        "available": WorkerAvailabilityStatus.AVAILABLE,
    }
    assert bookings.calls == 1


def test_availability_gate_returns_every_approved_time_off_conflict():
    time_off = TimeOffRepository([_time_off("request-b", "worker-1"), _time_off("request-a", "worker-1")])
    gate = AvailabilityGate(time_off)

    try:
        gate.ensure_no_approved_time_off(
            "worker-1", "venue-1", NOW - timedelta(minutes=30), NOW + timedelta(minutes=30)
        )
    except ApprovedTimeOffConflictError as exc:
        assert exc.request_ids == ("request-a", "request-b")
    else:
        raise AssertionError("Expected approved time off to block the booking.")

    assert time_off.last_query[3:] == ("venue-1", (TimeOffStatus.APPROVED,))

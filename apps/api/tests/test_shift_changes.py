from dataclasses import replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from apps.api.src.models.shift import Shift
from apps.api.src.models.worker_relationship import WorkerRelationship
from apps.api.src.repositories.booking_allocator import ShiftFullError
from apps.api.src.repositories.in_memory_booking_allocator import InMemoryBookingAllocator
from apps.api.src.repositories.in_memory_booking_repository import InMemoryBookingRepository
from apps.api.src.repositories.in_memory_booking_transition_repository import (
    InMemoryBookingTransitionRepository,
)
from apps.api.src.repositories.in_memory_shift_change_request_repository import (
    InMemoryShiftChangeRequestRepository,
    InMemoryShiftChangeTransitionRepository,
)
from apps.api.src.repositories.in_memory_shift_repository import InMemoryShiftRepository
from apps.api.src.repositories.in_memory_worker_relationship_repository import (
    InMemoryWorkerRelationshipRepository,
)
from apps.api.src.services.booking_ops import _decrement_workers_filled
from apps.api.src.services.errors import ConflictError, NotFoundError, ValidationError
from apps.api.src.services.shift_change_service import ShiftChangeService
from packages.domain.src.booking_state import BookingState

NOW = datetime(2030, 6, 3, 9, 0, tzinfo=UTC)
START = datetime(2030, 6, 10, 18, 0, tzinfo=UTC)
VENUE = "venue-1"


class RecordingOutbox:
    def __init__(self) -> None:
        self.notifications = []

    def publish_notification(self, **kwargs) -> None:
        self.notifications.append(kwargs)


class RecordingEscalations:
    def __init__(self) -> None:
        self.restarts = []

    def restart_ladder(self, shift_id: str, now: datetime) -> None:
        self.restarts.append((shift_id, now))


class RecordingRevisions:
    def __init__(self) -> None:
        self.minted = []
        self.notified = []

    def week_of(self, shift):
        return shift.start_time.date()

    def mint(self, venue_id, week_start, actor_user_id, now):
        outcome = (venue_id, week_start, actor_user_id)
        self.minted.append(outcome)
        return outcome

    def notify(self, outcome, exclude=None):
        self.notified.append((outcome, exclude or set()))


class FakeLifecycle:
    def __init__(self, bookings, shifts) -> None:
        self._bookings = bookings
        self._shifts = shifts
        self.cancellations = []

    def transition(self, booking_id, to_state, payload, actor_user_id, actor_role):
        booking = self._bookings.get(booking_id)
        self._bookings.save(
            replace(
                booking,
                state=to_state,
                cancelled_at=payload.now,
                cancellation_reason=payload.reason,
                cancelled_by_user_id=actor_user_id,
            )
        )
        _decrement_workers_filled(self._shifts, booking.shift_id, payload.now)
        self.cancellations.append((booking_id, payload.reason_code))
        return self._bookings.get(booking_id)


class Harness:
    def __init__(self) -> None:
        self.bookings = InMemoryBookingRepository()
        self.shifts = InMemoryShiftRepository(self.bookings)
        self.bookings.attach_shift_repo(self.shifts)
        self.requests = InMemoryShiftChangeRequestRepository()
        self.change_transitions = InMemoryShiftChangeTransitionRepository()
        self.relationships = InMemoryWorkerRelationshipRepository()
        self.booking_transitions = InMemoryBookingTransitionRepository()
        self.allocator = InMemoryBookingAllocator(self.bookings, self.shifts)
        self.outbox = RecordingOutbox()
        self.escalations = RecordingEscalations()
        self.revisions = RecordingRevisions()
        self.lifecycle = FakeLifecycle(self.bookings, self.shifts)
        self.service = ShiftChangeService(
            self.requests,
            self.change_transitions,
            self.shifts,
            self.bookings,
            self.allocator,
            self.relationships,
            self.booking_transitions,
            self.lifecycle,
            self.escalations,
            self.outbox,
            self.revisions,
        )

    def shift(self, shift_id: str = "shift-1", start=START, workers_needed: int = 1, **overrides) -> Shift:
        values = dict(
            shift_id=shift_id,
            operator_id="operator-1",
            account_id=VENUE,
            role="Bartender",
            location="Main bar",
            start_time=start,
            end_time=start + timedelta(hours=5),
            pay_rate=Decimal("14.50"),
            notes=None,
            status="open",
            created_at=NOW,
            workers_needed=workers_needed,
            workers_filled=0,
            origin="assigned",
            rota_state="published",
        )
        values.update(overrides)
        shift = Shift(**values)
        self.shifts.save(shift)
        return shift

    def relationship(self, worker_id: str, relationship_type: str = "pool", status: str = "active") -> None:
        self.relationships.save(
            WorkerRelationship(
                relationship_id=f"rel-{worker_id}",
                venue_id=VENUE,
                worker_id=worker_id,
                relationship_type=relationship_type,
                status=status,
                created_at=NOW,
                updated_at=NOW,
            )
        )

    def book(self, worker_id: str, shift_id: str = "shift-1"):
        outcome = self.allocator.allocate(shift_id, worker_id, NOW, f"booking-{worker_id}-{shift_id}")
        return outcome.booking


@pytest.fixture()
def harness() -> Harness:
    return Harness()


def test_a_release_needs_a_live_future_booking(harness):
    harness.shift()
    booking = harness.book("worker-1")
    with pytest.raises(NotFoundError):
        harness.service.request_release("worker-2", booking.booking_id, "family thing", NOW)
    with pytest.raises(ValidationError):
        harness.service.request_release("worker-1", booking.booking_id, "too late", START + timedelta(minutes=1))


def test_a_booking_holds_at_most_one_open_request(harness):
    harness.shift()
    booking = harness.book("worker-1")
    harness.service.request_release("worker-1", booking.booking_id, "family thing", NOW)
    with pytest.raises(ConflictError):
        harness.service.request_release("worker-1", booking.booking_id, "again", NOW)


def test_a_release_waits_for_the_manager_and_notifies_the_venue(harness):
    harness.shift()
    booking = harness.book("worker-1")
    request = harness.service.request_release("worker-1", booking.booking_id, "family thing", NOW)
    assert request.status == "pending_manager"
    assert harness.outbox.notifications[-1]["recipient_kind"] == "venue"


def test_an_approved_release_cancels_restarts_and_mints_one_revision(harness):
    harness.shift()
    booking = harness.book("worker-1")
    request = harness.service.request_release("worker-1", booking.booking_id, "family thing", NOW)

    approved = harness.service.approve(request.request_id, VENUE, "user-1", NOW)

    assert approved.status == "approved"
    assert harness.lifecycle.cancellations == [(booking.booking_id, "release_approved")]
    assert harness.escalations.restarts == [("shift-1", NOW)]
    assert len(harness.revisions.minted) == 1
    assert harness.revisions.notified[0][1] == {"worker-1"}
    assert harness.shifts.get("shift-1").rota_state == "published"


def test_cover_must_name_an_active_non_one_off_colleague(harness):
    harness.shift()
    booking = harness.book("worker-1")
    with pytest.raises(ValidationError):
        harness.service.request_cover("worker-1", booking.booking_id, "worker-1", "swap", NOW)
    with pytest.raises(ValidationError):
        harness.service.request_cover("worker-1", booking.booking_id, "worker-2", "swap", NOW)
    harness.relationship("worker-2", "one_off")
    with pytest.raises(ValidationError):
        harness.service.request_cover("worker-1", booking.booking_id, "worker-2", "swap", NOW)


def test_cover_asks_the_replacement_first(harness):
    harness.shift()
    booking = harness.book("worker-1")
    harness.relationship("worker-2")
    request = harness.service.request_cover("worker-1", booking.booking_id, "worker-2", "swap", NOW)
    assert request.status == "pending_replacement"
    last = harness.outbox.notifications[-1]
    assert (last["recipient_kind"], last["recipient_id"]) == ("worker", "worker-2")
    with pytest.raises(ValidationError):
        harness.service.approve(request.request_id, VENUE, "user-1", NOW)


def test_the_replacement_accepting_sends_it_to_the_manager(harness):
    harness.shift()
    booking = harness.book("worker-1")
    harness.relationship("worker-2")
    request = harness.service.request_cover("worker-1", booking.booking_id, "worker-2", "swap", NOW)

    with pytest.raises(NotFoundError):
        harness.service.accept_replacement(request.request_id, "worker-3", NOW)
    moved = harness.service.accept_replacement(request.request_id, "worker-2", NOW)

    assert moved.status == "pending_manager"
    assert harness.outbox.notifications[-1]["recipient_kind"] == "venue"


def test_the_replacement_declining_settles_the_request(harness):
    harness.shift()
    booking = harness.book("worker-1")
    harness.relationship("worker-2")
    request = harness.service.request_cover("worker-1", booking.booking_id, "worker-2", "swap", NOW)

    declined = harness.service.decline_replacement(request.request_id, "worker-2", NOW)

    assert declined.status == "declined"
    last = harness.outbox.notifications[-1]
    assert (last["recipient_kind"], last["recipient_id"]) == ("worker", "worker-1")
    fresh = harness.service.request_release("worker-1", booking.booking_id, "release then", NOW)
    assert fresh.status == "pending_manager"


def test_an_approved_cover_swaps_the_worker_on_the_same_slot(harness):
    harness.shift(workers_needed=1)
    booking = harness.book("worker-1")
    harness.relationship("worker-1")
    harness.relationship("worker-2", "bank")
    request = harness.service.request_cover("worker-1", booking.booking_id, "worker-2", "swap", NOW)
    harness.service.accept_replacement(request.request_id, "worker-2", NOW)

    approved = harness.service.approve(request.request_id, VENUE, "user-1", NOW)

    assert approved.status == "approved"
    assert harness.bookings.get(booking.booking_id).state == BookingState.CANCELLED_BY_OPERATOR
    live = [
        b for b in harness.bookings.list_by_shift("shift-1")
        if b.state == BookingState.CONFIRMED
    ]
    assert [b.worker_id for b in live] == ["worker-2"]
    assert live[0].attendance_mode == "employed"
    assert harness.escalations.restarts == []
    assert len(harness.revisions.minted) == 1
    assert harness.revisions.notified[0][1] == {"worker-1", "worker-2"}
    recorded = harness.booking_transitions.list_for_booking(live[0].booking_id)
    assert recorded[-1].reason_code == "cover_approved"


def test_a_replacement_with_an_overlap_blocks_approval_before_anything_moves(harness):
    harness.shift()
    harness.shift("shift-2", start=START + timedelta(hours=2))
    booking = harness.book("worker-1")
    harness.relationship("worker-2")
    harness.book("worker-2", "shift-2")
    request = harness.service.request_cover("worker-1", booking.booking_id, "worker-2", "swap", NOW)
    harness.service.accept_replacement(request.request_id, "worker-2", NOW)

    with pytest.raises(ValidationError):
        harness.service.approve(request.request_id, VENUE, "user-1", NOW)

    assert harness.bookings.get(booking.booking_id).state == BookingState.CONFIRMED
    assert harness.lifecycle.cancellations == []
    assert harness.revisions.minted == []


def test_a_failed_allocation_surfaces_as_a_conflict(harness, monkeypatch):
    harness.shift()
    booking = harness.book("worker-1")
    harness.relationship("worker-2")
    request = harness.service.request_cover("worker-1", booking.booking_id, "worker-2", "swap", NOW)
    harness.service.accept_replacement(request.request_id, "worker-2", NOW)

    def boom(*args, **kwargs):
        raise ShiftFullError("shift-1")

    monkeypatch.setattr(harness.allocator, "allocate", boom)
    with pytest.raises(ConflictError):
        harness.service.approve(request.request_id, VENUE, "user-1", NOW)
    assert harness.shifts.get("shift-1").rota_state == "published"


def test_withdrawing_and_declining_close_the_request(harness):
    harness.shift()
    booking = harness.book("worker-1")
    request = harness.service.request_release("worker-1", booking.booking_id, "family thing", NOW)
    withdrawn = harness.service.withdraw(request.request_id, "worker-1", NOW)
    assert withdrawn.status == "withdrawn"

    second = harness.service.request_release("worker-1", booking.booking_id, "second try", NOW)
    declined = harness.service.decline(second.request_id, VENUE, "user-1", NOW)
    assert declined.status == "declined"
    assert harness.bookings.get(booking.booking_id).state == BookingState.CONFIRMED
    with pytest.raises(NotFoundError):
        harness.service.decline(second.request_id, "venue-2", "user-1", NOW)


def test_expiry_closes_requests_whose_booking_started_or_moved_on(harness):
    harness.shift()
    harness.shift("shift-2", start=START + timedelta(days=2))
    started = harness.book("worker-1")
    future = harness.book("worker-1", "shift-2")
    harness.service.request_release("worker-1", started.booking_id, "family thing", NOW)
    kept = harness.service.request_release("worker-1", future.booking_id, "other thing", NOW)

    expired = harness.service.expire_due(START + timedelta(minutes=1))

    assert expired == 1
    statuses = {r.status for r in harness.service.list_requests_for_worker("worker-1")}
    assert statuses == {"expired", "pending_manager"}
    assert harness.requests.get(kept.request_id).status == "pending_manager"


def test_the_venue_queue_filters_by_status(harness):
    harness.shift()
    booking = harness.book("worker-1")
    request = harness.service.request_release("worker-1", booking.booking_id, "family thing", NOW)
    assert [r.request_id for r in harness.service.list_requests_for_venue(VENUE, "pending_manager")] == [
        request.request_id
    ]
    assert harness.service.list_requests_for_venue(VENUE, "approved") == []
    assert harness.service.list_requests_for_venue("venue-2") == []


def test_the_replacement_sees_the_request_in_their_list(harness):
    harness.shift()
    booking = harness.book("worker-1")
    harness.relationship("worker-2")
    request = harness.service.request_cover("worker-1", booking.booking_id, "worker-2", "swap", NOW)
    assert [r.request_id for r in harness.service.list_requests_for_worker("worker-2")] == [
        request.request_id
    ]

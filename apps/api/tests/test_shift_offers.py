from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from apps.api.src.models.shift import Shift
from apps.api.src.models.worker_relationship import WorkerRelationship
from apps.api.src.repositories.in_memory_booking_allocator import InMemoryBookingAllocator
from apps.api.src.repositories.in_memory_booking_repository import InMemoryBookingRepository
from apps.api.src.repositories.in_memory_booking_transition_repository import (
    InMemoryBookingTransitionRepository,
)
from apps.api.src.repositories.in_memory_shift_offer_repository import InMemoryShiftOfferRepository
from apps.api.src.repositories.in_memory_shift_repository import InMemoryShiftRepository
from apps.api.src.repositories.in_memory_worker_relationship_repository import (
    InMemoryWorkerRelationshipRepository,
)
from apps.api.src.repositories.shift_offer_repository import DuplicatePendingOfferError
from apps.api.src.services.errors import NotFoundError, ValidationError
from apps.api.src.services.shift_offer_service import ShiftOfferService

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


class Harness:
    def __init__(self) -> None:
        self.bookings = InMemoryBookingRepository()
        self.shifts = InMemoryShiftRepository(self.bookings)
        self.bookings.attach_shift_repo(self.shifts)
        self.offers = InMemoryShiftOfferRepository()
        self.relationships = InMemoryWorkerRelationshipRepository()
        self.transitions = InMemoryBookingTransitionRepository()
        self.outbox = RecordingOutbox()
        self.escalations = RecordingEscalations()
        self.service = ShiftOfferService(
            self.offers,
            self.shifts,
            InMemoryBookingAllocator(self.bookings, self.shifts),
            self.relationships,
            self.transitions,
            self.escalations,
            self.outbox,
        )

    def shift(self, shift_id: str = "shift-1", worker_id: str = "worker-1", **overrides) -> Shift:
        values = dict(
            shift_id=shift_id,
            operator_id="operator-1",
            account_id=VENUE,
            role="Bartender",
            location="Main bar",
            start_time=START,
            end_time=START + timedelta(hours=5),
            pay_rate=Decimal("14.50"),
            notes=None,
            status="open",
            created_at=NOW,
            workers_needed=1,
            workers_filled=0,
            origin="assigned",
            assigned_worker_id=worker_id,
            rota_state="published",
        )
        values.update(overrides)
        shift = Shift(**values)
        self.shifts.save(shift)
        return shift

    def relationship(self, relationship_type: str, worker_id: str = "worker-1") -> None:
        self.relationships.save(
            WorkerRelationship(
                relationship_id=f"rel-{worker_id}",
                venue_id=VENUE,
                worker_id=worker_id,
                relationship_type=relationship_type,
                status="active",
                created_at=NOW,
                updated_at=NOW,
            )
        )


@pytest.fixture()
def harness() -> Harness:
    return Harness()


def test_a_shift_holds_at_most_one_pending_offer(harness):
    shift = harness.shift()
    harness.service.offer(shift, "worker-1", "rota", NOW, None)
    with pytest.raises(DuplicatePendingOfferError):
        harness.service.offer(shift, "worker-2", "manual", NOW, None)


def test_accepting_books_through_the_allocator_and_closes_the_offer(harness):
    shift = harness.shift()
    harness.relationship("pool")
    offer = harness.service.offer(shift, "worker-1", "rota", NOW, None)

    booking = harness.service.accept(offer.offer_id, "worker-1", NOW)

    assert booking.worker_id == "worker-1"
    assert booking.attendance_mode == "pin"
    stored = harness.offers.get(offer.offer_id)
    assert (stored.status, stored.response_source) == ("accepted", "manual")
    transitions = harness.transitions.list_for_booking(booking.booking_id)
    assert [t.reason_code for t in transitions] == ["offer_accepted"]
    assert transitions[0].context["offer_id"] == offer.offer_id
    assert [n["event_type"] for n in harness.outbox.notifications] == ["offer.accepted"]
    assert harness.shifts.get(shift.shift_id).workers_filled == 1


def test_an_employed_acceptance_freezes_the_employed_attendance_mode(harness):
    shift = harness.shift()
    harness.relationship("permanent")
    offer = harness.service.offer(shift, "worker-1", "cover", NOW, None)

    booking = harness.service.accept(offer.offer_id, "worker-1", NOW, response_source="auto")

    assert booking.attendance_mode == "employed"
    assert harness.offers.get(offer.offer_id).response_source == "auto"


def test_accepting_an_expired_offer_closes_it(harness):
    shift = harness.shift()
    harness.relationship("pool")
    offer = harness.service.offer(shift, "worker-1", "rota", NOW, NOW + timedelta(hours=12))

    with pytest.raises(ValidationError, match="expired"):
        harness.service.accept(offer.offer_id, "worker-1", NOW + timedelta(hours=13))

    assert harness.offers.get(offer.offer_id).status == "expired"
    assert harness.bookings.list_by_worker("worker-1") == []


def test_a_reassigned_shift_refuses_its_old_offer(harness):
    shift = harness.shift()
    harness.relationship("pool")
    offer = harness.service.offer(shift, "worker-1", "rota", NOW, None)
    harness.shift(shift_id=shift.shift_id, worker_id="worker-2")

    with pytest.raises(ValidationError, match="moved on"):
        harness.service.accept(offer.offer_id, "worker-1", NOW)


def test_a_filled_shift_refuses_acceptance(harness):
    shift = harness.shift(workers_needed=1, workers_filled=1, status="filled")
    harness.relationship("pool")
    offer = harness.service.offer(shift, "worker-1", "rota", NOW, None)

    with pytest.raises(ValidationError, match="moved on"):
        harness.service.accept(offer.offer_id, "worker-1", NOW)


def test_declining_restarts_the_ladder_and_notifies_the_venue(harness):
    shift = harness.shift()
    harness.relationship("pool")
    offer = harness.service.offer(shift, "worker-1", "rota", NOW, None)

    declined = harness.service.decline(offer.offer_id, "worker-1", NOW)

    assert declined.status == "declined"
    assert harness.escalations.restarts == [(shift.shift_id, NOW)]
    assert [n["event_type"] for n in harness.outbox.notifications] == ["offer.declined"]


def test_only_the_named_worker_can_answer_and_only_once(harness):
    shift = harness.shift()
    harness.relationship("pool")
    offer = harness.service.offer(shift, "worker-1", "rota", NOW, None)

    with pytest.raises(NotFoundError):
        harness.service.accept(offer.offer_id, "worker-2", NOW)

    harness.service.decline(offer.offer_id, "worker-1", NOW)
    with pytest.raises(ValidationError, match="answered"):
        harness.service.accept(offer.offer_id, "worker-1", NOW)
    assert harness.escalations.restarts == [(shift.shift_id, NOW)]

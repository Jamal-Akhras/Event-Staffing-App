from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from apps.api.src.jobs.run_auto_accept_sweep import sweep_auto_accept
from apps.api.src.models.auto_accept import WorkerAutoAcceptRule
from apps.api.src.models.shift import Shift
from apps.api.src.models.worker_certification import WorkerCertification
from apps.api.src.models.worker_relationship import WorkerRelationship
from apps.api.src.repositories.in_memory_auto_accept_repository import (
    InMemoryAutoAcceptAttemptRepository,
    InMemoryWorkerAutoAcceptRuleRepository,
)
from apps.api.src.repositories.in_memory_booking_allocator import InMemoryBookingAllocator
from apps.api.src.repositories.in_memory_booking_repository import InMemoryBookingRepository
from apps.api.src.repositories.in_memory_booking_transition_repository import (
    InMemoryBookingTransitionRepository,
)
from apps.api.src.repositories.in_memory_shift_offer_repository import (
    InMemoryShiftOfferRepository,
)
from apps.api.src.repositories.in_memory_shift_repository import InMemoryShiftRepository
from apps.api.src.repositories.in_memory_worker_certification_repository import (
    InMemoryWorkerCertificationRepository,
)
from apps.api.src.repositories.in_memory_worker_relationship_repository import (
    InMemoryWorkerRelationshipRepository,
)
from apps.api.src.services.auto_accept_service import AutoAcceptService
from apps.api.src.services.certification_gate import CertificationGate
from apps.api.src.services.errors import NotFoundError, ValidationError
from apps.api.src.services.shift_offer_service import ShiftOfferService

NOW = datetime(2030, 6, 3, 9, 0, tzinfo=UTC)
START = datetime(2030, 6, 10, 18, 0, tzinfo=UTC)
VENUE = "venue-1"


class RecordingOutbox:
    def __init__(self) -> None:
        self.notifications: list[dict] = []

    def publish_notification(self, **kwargs) -> None:
        self.notifications.append(kwargs)


class RecordingEscalations:
    def restart_ladder(self, shift_id: str, now: datetime) -> None:
        raise AssertionError("Auto-accept must not restart the escalation ladder.")


class Harness:
    def __init__(self) -> None:
        self.bookings = InMemoryBookingRepository()
        self.shifts = InMemoryShiftRepository(self.bookings)
        self.bookings.attach_shift_repo(self.shifts)
        self.offers = InMemoryShiftOfferRepository()
        self.rules = InMemoryWorkerAutoAcceptRuleRepository()
        self.attempts = InMemoryAutoAcceptAttemptRepository(self.offers)
        self.relationships = InMemoryWorkerRelationshipRepository()
        self.transitions = InMemoryBookingTransitionRepository()
        self.certifications = InMemoryWorkerCertificationRepository()
        self.outbox = RecordingOutbox()
        self.offer_service = ShiftOfferService(
            self.offers,
            self.shifts,
            InMemoryBookingAllocator(self.bookings, self.shifts),
            self.relationships,
            self.transitions,
            RecordingEscalations(),
            self.outbox,
            CertificationGate(self.certifications),
        )
        self.service = AutoAcceptService(
            self.rules,
            self.attempts,
            self.offers,
            self.shifts,
            self.relationships,
            self.offer_service,
        )

    def relationship(
        self,
        relationship_type: str = "pool",
        status: str = "active",
        worker_id: str = "worker-1",
        venue_id: str = VENUE,
    ) -> WorkerRelationship:
        relationship = WorkerRelationship(
            relationship_id=f"rel-{worker_id}-{venue_id}",
            venue_id=venue_id,
            worker_id=worker_id,
            relationship_type=relationship_type,
            status=status,
            created_at=NOW,
            updated_at=NOW,
        )
        return self.relationships.save(relationship)

    def shift(
        self,
        shift_id: str = "shift-1",
        worker_id: str | None = "worker-1",
        **overrides,
    ) -> Shift:
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
        return self.shifts.save(Shift(**values))

    def named_offer(self, **shift_overrides):
        shift = self.shift(**shift_overrides)
        return self.offer_service.offer(shift, "worker-1", "rota", NOW, START)

    def rule(
        self,
        enabled: bool = True,
        roles: list[str] | None = None,
        minimum_rate: Decimal | None = None,
        minimum_notice_hours: int | None = None,
        now: datetime = NOW,
    ) -> WorkerAutoAcceptRule:
        return self.service.upsert_rule(
            "worker-1",
            VENUE,
            enabled,
            [] if roles is None else roles,
            minimum_rate,
            minimum_notice_hours,
            now,
        )


@pytest.fixture()
def harness() -> Harness:
    return Harness()


@pytest.mark.parametrize(
    ("relationship_type", "status"),
    [("permanent", "active"), ("one_off", "active"), ("pool", "ended")],
)
def test_only_an_active_pool_relationship_can_enable_a_rule(
    harness, relationship_type, status
):
    harness.relationship(relationship_type, status)

    with pytest.raises(ValidationError, match="active pool"):
        harness.rule()


def test_foreign_venue_rule_creation_is_not_found(harness):
    with pytest.raises(NotFoundError):
        harness.rule(enabled=False)


def test_rule_edits_bump_version_and_disabling_and_deleting_remain_allowed(harness):
    harness.relationship()
    first = harness.rule(roles=[" Bartender "])
    harness.relationship(status="ended")

    second = harness.rule(enabled=False, roles=[], now=NOW + timedelta(hours=1))

    assert second.rule_id == first.rule_id
    assert second.version == 2
    assert second.created_at == first.created_at
    assert second.updated_at == NOW + timedelta(hours=1)
    harness.service.delete_rule("worker-1", VENUE)
    with pytest.raises(NotFoundError):
        harness.service.get_rule("worker-1", VENUE)


def test_no_rule_and_disabled_rule_are_stable_skips(harness):
    offer = harness.named_offer()
    missing = harness.service.evaluate_offer(offer, NOW)
    assert (missing.outcome, missing.reason, missing.rule_version) == (
        "skipped",
        "no_rule",
        0,
    )

    harness.relationship()
    harness.rule(enabled=False)
    disabled = harness.service.evaluate_offer(offer, NOW + timedelta(minutes=1))
    assert (disabled.outcome, disabled.reason, disabled.rule_version) == (
        "skipped",
        "rule_disabled",
        1,
    )


def test_role_matching_is_trimmed_case_insensitive_and_empty_means_any(harness):
    harness.relationship()
    offer = harness.named_offer(role="  Bartender  ")
    harness.rule(roles=[" bArTeNdEr "])

    accepted = harness.service.evaluate_offer(offer, NOW)

    assert accepted.outcome == "accepted"
    assert accepted.rule_snapshot["roles"] == ["bArTeNdEr"]


def test_role_mismatch_skips(harness):
    harness.relationship()
    offer = harness.named_offer()
    harness.rule(roles=["Server"])

    attempt = harness.service.evaluate_offer(offer, NOW)

    assert (attempt.outcome, attempt.reason) == ("skipped", "role_mismatch")
    assert harness.offers.get(offer.offer_id).status == "pending"


def test_rate_below_minimum_skips(harness):
    harness.relationship()
    offer = harness.named_offer()
    harness.rule(minimum_rate=Decimal("15.00"))

    attempt = harness.service.evaluate_offer(offer, NOW)

    assert (attempt.outcome, attempt.reason) == (
        "skipped",
        "rate_below_minimum",
    )


def test_notice_too_short_skips(harness):
    harness.relationship()
    offer = harness.named_offer(start_time=NOW + timedelta(hours=5))
    harness.rule(minimum_notice_hours=6)

    attempt = harness.service.evaluate_offer(offer, NOW)

    assert (attempt.outcome, attempt.reason) == ("skipped", "notice_too_short")


def test_acceptance_uses_the_shared_allocator_and_closes_the_offer(harness):
    harness.relationship()
    offer = harness.named_offer()
    harness.rule()

    attempt = harness.service.evaluate_offer(offer, NOW)

    stored_offer = harness.offers.get(offer.offer_id)
    bookings = harness.bookings.list_by_worker("worker-1")
    assert (attempt.outcome, attempt.reason) == ("accepted", None)
    assert len(bookings) == 1
    assert (stored_offer.status, stored_offer.response_source) == ("accepted", "auto")
    assert harness.shifts.get(offer.shift_id).workers_filled == 1
    transition = harness.transitions.list_for_booking(bookings[0].booking_id)[0]
    assert transition.context["response_source"] == "auto"


def test_same_version_replays_the_attempt_without_touching_the_offer(harness):
    harness.relationship()
    offer = harness.named_offer()
    harness.rule()
    first = harness.service.evaluate_offer(offer, NOW)

    replay = harness.service.evaluate_offer(offer, NOW + timedelta(hours=1))

    assert replay == first
    assert len(harness.bookings.list_by_worker("worker-1")) == 1
    assert harness.attempts.list_for_worker("worker-1", 25) == [first]


def test_a_version_bump_re_evaluates_a_still_pending_offer(harness):
    harness.relationship()
    offer = harness.named_offer()
    harness.rule(roles=["Server"])
    first = harness.service.evaluate_offer(offer, NOW)
    updated = harness.rule(roles=["Bartender"], now=NOW + timedelta(minutes=1))

    second = harness.service.evaluate_offer(offer, NOW + timedelta(minutes=1))

    assert (first.outcome, first.rule_version) == ("skipped", 1)
    assert (second.outcome, second.rule_version) == ("accepted", 2)
    assert updated.version == 2
    assert len(harness.attempts.list_for_worker("worker-1", 25)) == 2


def test_missing_certification_skips_and_leaves_the_offer_pending(harness):
    harness.relationship()
    offer = harness.named_offer(required_certification="Personal Licence")
    harness.rule()

    attempt = harness.service.evaluate_offer(offer, NOW)

    assert (attempt.outcome, attempt.reason) == (
        "skipped",
        "missing_certification",
    )
    assert harness.offers.get(offer.offer_id).status == "pending"
    assert harness.bookings.list_by_worker("worker-1") == []

    harness.certifications.save(
        WorkerCertification(
            certification_id="cert-1",
            worker_id="worker-1",
            name="personal licence",
            display_name="Personal Licence",
            expires_at=START + timedelta(days=1),
            created_at=NOW,
            updated_at=NOW,
        )
    )
    harness.rule(now=NOW + timedelta(minutes=1))
    assert harness.service.evaluate_offer(offer, NOW + timedelta(minutes=1)).outcome == "accepted"


def test_offer_acceptance_errors_are_recorded_as_failed(harness, monkeypatch):
    harness.relationship()
    offer = harness.named_offer()
    harness.rule()

    def reject(*args, **kwargs):
        raise ValidationError("This shift has already been filled.")

    monkeypatch.setattr(harness.offer_service, "accept", reject)
    attempt = harness.service.evaluate_offer(offer, NOW)

    assert (attempt.outcome, attempt.reason) == (
        "failed",
        "This shift has already been filled.",
    )
    assert harness.offers.get(offer.offer_id).status == "pending"


def test_pool_broadcast_without_a_named_offer_is_never_booked_by_the_sweep(harness):
    harness.relationship()
    harness.rule()
    harness.shift(origin="pool", assigned_worker_id=None)

    evaluated = sweep_auto_accept(harness.service, NOW)

    assert evaluated == 0
    assert harness.bookings.list_by_worker("worker-1") == []


def test_one_offer_failure_does_not_abort_the_sweep(harness, monkeypatch):
    harness.relationship()
    first = harness.named_offer(shift_id="shift-1")
    second_shift = harness.shift(shift_id="shift-2")
    second = harness.offer_service.offer(second_shift, "worker-1", "rota", NOW, START)
    harness.rule()
    original = harness.service.evaluate_offer

    def evaluate(offer, now):
        if offer.offer_id == first.offer_id:
            raise RuntimeError("isolated failure")
        return original(offer, now)

    monkeypatch.setattr(harness.service, "evaluate_offer", evaluate)

    assert sweep_auto_accept(harness.service, NOW) == 1
    assert harness.offers.get(second.offer_id).status == "accepted"


def test_scheduler_registers_the_one_minute_auto_accept_job():
    from apps.api.src.scheduler import create_scheduler

    scheduler = create_scheduler()
    job = scheduler.get_job("auto_accept_sweep")

    assert job is not None
    assert job.trigger.interval == timedelta(minutes=1)

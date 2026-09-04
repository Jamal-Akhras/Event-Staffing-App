from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from apps.api.src.models.availability import AvailabilityRule
from apps.api.src.models.booking_charge import BookingCharge
from apps.api.src.models.organisation import Organisation, Venue
from apps.api.src.models.shift import Shift
from apps.api.src.models.worker_relationship import WorkerRelationship
from apps.api.src.repositories.in_memory_availability_repository import (
    InMemoryAvailabilityExceptionRepository,
    InMemoryAvailabilityRuleRepository,
    InMemoryTimeOffRepository,
)
from apps.api.src.repositories.in_memory_booking_charge_repository import (
    InMemoryBookingChargeRepository,
)
from apps.api.src.repositories.in_memory_booking_repository import InMemoryBookingRepository
from apps.api.src.repositories.in_memory_commercial_repository import (
    InMemoryCommercialAgreementRepository,
)
from apps.api.src.repositories.in_memory_organisation_repository import (
    InMemoryOrganisationRepository,
)
from apps.api.src.repositories.in_memory_shift_repository import InMemoryShiftRepository
from apps.api.src.repositories.in_memory_worker_relationship_repository import (
    InMemoryWorkerRelationshipRepository,
)
from apps.api.src.services.availability_service import AvailabilityService
from apps.api.src.services.insight_aggregates_service import InsightAggregatesService

NOW = datetime(2030, 6, 3, 9, 0, tzinfo=UTC)
VENUE = "venue-1"


def _harness():
    charges = InMemoryBookingChargeRepository()
    bookings = InMemoryBookingRepository()
    shifts = InMemoryShiftRepository(bookings)
    relationships = InMemoryWorkerRelationshipRepository()
    rules = InMemoryAvailabilityRuleRepository()
    exceptions = InMemoryAvailabilityExceptionRepository()
    time_off = InMemoryTimeOffRepository()
    organisations = InMemoryOrganisationRepository()
    agreements = InMemoryCommercialAgreementRepository()
    organisations.save_organisation(
        Organisation(organisation_id="org-1", name="Group", country="GB", currency="GBP", created_at=NOW)
    )
    organisations.save_venue(
        Venue(venue_id=VENUE, organisation_id="org-1", name="V", country="GB", currency="GBP",
              created_at=NOW, market_id="bath-gb")
    )
    availability = AvailabilityService(rules, exceptions, time_off, bookings)
    service = InsightAggregatesService(
        charges, shifts, bookings, relationships, availability, organisations, agreements
    )
    return service, charges, shifts, relationships, rules


def _charge(charge_id: str, fee_basis: str, hours: str, wages: str, fee: str) -> BookingCharge:
    return BookingCharge(
        charge_id=charge_id,
        booking_id=f"bk-{charge_id}",
        shift_id=f"sh-{charge_id}",
        account_id=VENUE,
        worker_id=f"w-{charge_id}",
        worker_name="Worker",
        role="Bartender",
        period="2030-06",
        start_time=NOW,
        end_time=NOW + timedelta(hours=5),
        completed_at=NOW,
        hours=Decimal(hours),
        pay_rate=Decimal("14.00"),
        wages=Decimal(wages),
        fee_percent=Decimal("10.00"),
        fee=Decimal(fee),
        total=Decimal(wages) + Decimal(fee),
        currency="GBP",
        fee_waived=False,
        waiver_code=None,
        recorded_at=NOW,
        worker_relationship="pool",
        fee_basis=fee_basis,
        plan="classic",
    )


def test_cost_of_coverage_splits_by_source_with_per_hour(_h=None):
    service, charges, *_ = _harness()
    charges.record(_charge("a", "venue_employed", "5", "70.00", "0.00"))
    charges.record(_charge("b", "venue_pool", "4", "56.00", "5.60"))
    charges.record(_charge("c", "outside", "3", "42.00", "4.20"))

    cost = service.cost_of_coverage(VENUE, "2030-06")
    by_source = {source.source: source for source in cost.sources}
    assert by_source["team"].fees == Decimal("0.00")
    assert by_source["team"].cost_per_hour == Decimal("14.00")
    assert by_source["pool"].fees == Decimal("5.60")
    assert by_source["market"].fees == Decimal("4.20")
    assert cost.fees == Decimal("9.80")
    assert cost.hours == Decimal("12.00")


def test_cost_of_coverage_is_empty_with_no_charges():
    service, *_ = _harness()
    cost = service.cost_of_coverage(VENUE, "2030-06")
    assert cost.fees == Decimal("0.00")
    assert cost.cost_per_hour is None
    assert all(source.shifts == 0 for source in cost.sources)


def _shift(shift_id: str, start, **overrides) -> Shift:
    values = dict(
        shift_id=shift_id, operator_id="op-1", account_id=VENUE, role="Bartender",
        location="Bar", start_time=start, end_time=start + timedelta(hours=5),
        pay_rate=Decimal("14.00"), notes=None, status="open", created_at=NOW,
        workers_needed=1, workers_filled=0, origin="pool",
    )
    values.update(overrides)
    return Shift(**values)


def _member(worker_id: str, relationship_type: str) -> WorkerRelationship:
    return WorkerRelationship(
        relationship_id=f"rel-{worker_id}", venue_id=VENUE, worker_id=worker_id,
        relationship_type=relationship_type, status="active", created_at=NOW, updated_at=NOW,
    )


def test_savings_available_flags_shifts_an_available_team_member_could_cover():
    service, charges, shifts, relationships, rules = _harness()
    start = NOW + timedelta(days=2)
    shifts.save(_shift("sh-open", start))
    relationships.save(_member("worker-1", "permanent"))
    rules.save(
        AvailabilityRule(
            rule_id="rule-1", worker_id="worker-1", timezone="Europe/London",
            weekday=start.weekday(), start_minute=0, duration_minutes=1439,
            effective_from=start.date(), effective_until=None, created_at=NOW, updated_at=NOW,
        )
    )

    result = service.savings_available(VENUE, NOW)
    assert [o.shift_id for o in result.opportunities] == ["sh-open"]
    assert result.opportunities[0].available_candidates == 1
    assert result.opportunities[0].fee_avoided == Decimal("5.60")
    assert result.total_fee_avoided == Decimal("5.60")


def test_savings_available_is_empty_without_available_members():
    service, charges, shifts, relationships, rules = _harness()
    shifts.save(_shift("sh-open", NOW + timedelta(days=2)))
    result = service.savings_available(VENUE, NOW)
    assert result.opportunities == []
    assert result.total_fee_avoided == Decimal("0.00")


def _booking(shift_id: str, state, source: str):
    from packages.domain.src.booking import Booking

    return Booking(
        booking_id=f"bk-{shift_id}", shift_id=shift_id, worker_id="w-1", operator_id="op-1",
        start_time=NOW, end_time=NOW + timedelta(hours=5), state=state, created_at=NOW,
        allocation_source=source,
    )


def test_what_helps_fill_buckets_by_lead_time_with_denominators_and_insufficient_data():
    from packages.domain.src.booking_state import BookingState

    service, charges, shifts, relationships, rules = _harness()
    bookings = service._bookings
    # 5 well-ahead shifts (created 20d before start), 4 filled -> sufficient sample
    for index in range(5):
        start = NOW - timedelta(days=1) + timedelta(hours=index)
        created = start - timedelta(days=20)
        shifts.save(_shift(f"ahead-{index}", start, created_at=created, status="open"))
        if index < 4:
            bookings.save(_booking(f"ahead-{index}", BookingState.CHECKED_IN, "pool"))
    # 2 last-minute shifts (created 1d before) -> below MIN_SAMPLE
    for index in range(2):
        start = NOW - timedelta(hours=index + 1)
        shifts.save(_shift(f"late-{index}", start, created_at=start - timedelta(days=1), status="open"))

    factors = service.what_helps_fill(VENUE, NOW)
    lead = {bucket.label: bucket for bucket in factors.by_lead_time}
    assert lead["14d+"].shifts == 5
    assert lead["14d+"].filled == 4
    assert lead["14d+"].fill_rate == Decimal("80.00")
    assert lead["<2d"].shifts == 2
    assert lead["<2d"].fill_rate is None  # below minimum sample


def test_value_of_planning_reports_fill_and_escalation_depth_by_lead():
    from packages.domain.src.booking_state import BookingState

    service, charges, shifts, relationships, rules = _harness()
    bookings = service._bookings
    for index in range(5):
        start = NOW - timedelta(days=1) + timedelta(hours=index)
        shifts.save(_shift(f"ahead-{index}", start, created_at=start - timedelta(days=20), status="open"))
        source = "team" if index < 3 else "market"
        if index < 4:
            bookings.save(_booking(f"ahead-{index}", BookingState.APPROVED, source))

    value = service.value_of_planning(VENUE, NOW)
    by_lead = {bucket.label: bucket for bucket in value.by_posting_lead}
    ahead = by_lead["14d+"]
    assert ahead.shifts == 5
    assert ahead.filled == 4
    assert ahead.fill_rate == Decimal("80.00")
    # three team (depth 0) + one market (depth 2) filled -> avg 0.5
    assert ahead.average_escalation_depth == Decimal("0.50")

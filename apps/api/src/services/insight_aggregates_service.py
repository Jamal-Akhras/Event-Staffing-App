from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal

from apps.api.src.models.worker_relationship import EMPLOYED_TYPES
from apps.api.src.repositories.booking_charge_repository import BookingChargeRepository
from apps.api.src.repositories.booking_repository import BookingRepository
from apps.api.src.repositories.organisation_repository import OrganisationRepository
from apps.api.src.repositories.shift_repository import ShiftRepository
from apps.api.src.repositories.worker_relationship_repository import WorkerRelationshipRepository
from apps.api.src.services.availability_service import AvailabilityService
from apps.api.src.services.billing_math import money
from apps.api.src.services.commercial_service import agreement_as_of, fee_percent_for
from apps.api.src.repositories.commercial_repository import CommercialAgreementRepository
from packages.domain.src.booking_state import BookingState

SOURCE_OF_BASIS = {
    "venue_employed": "team",
    "organisation_employed": "team",
    "venue_pool": "pool",
    "outside": "market",
}
ZERO = Decimal("0.00")
MIN_SAMPLE = 4
CHECKED_IN_STATES = frozenset(
    {
        BookingState.CHECKED_IN,
        BookingState.CHECKED_OUT,
        BookingState.APPROVED,
        BookingState.PAID,
    }
)
SOURCE_DEPTH = {
    "assigned": 0,
    "named": 0,
    "team": 0,
    "cover": 0,
    "pool": 1,
    "market": 2,
}


@dataclass(frozen=True)
class SourceCost:
    source: str
    shifts: int
    hours: Decimal
    wages: Decimal
    fees: Decimal
    cost_per_hour: Decimal | None


@dataclass(frozen=True)
class CoverageCost:
    period: str
    sources: list[SourceCost]
    hours: Decimal
    wages: Decimal
    fees: Decimal
    cost_per_hour: Decimal | None


@dataclass(frozen=True)
class SavingOpportunity:
    shift_id: str
    role: str
    start_time: datetime
    available_candidates: int
    fee_avoided: Decimal


@dataclass(frozen=True)
class SavingsAvailable:
    opportunities: list[SavingOpportunity]
    total_fee_avoided: Decimal


@dataclass(frozen=True)
class FillBucket:
    label: str
    shifts: int
    filled: int
    fill_rate: Decimal | None


@dataclass(frozen=True)
class FillFactors:
    lookback_days: int
    by_lead_time: list[FillBucket]
    by_weekday: list[FillBucket]
    by_pay_band: list[FillBucket]


@dataclass(frozen=True)
class PlanningBucket:
    label: str
    shifts: int
    filled: int
    fill_rate: Decimal | None
    average_escalation_depth: Decimal | None


@dataclass(frozen=True)
class PlanningValue:
    lookback_days: int
    by_posting_lead: list[PlanningBucket]


class InsightAggregatesService:
    def __init__(
        self,
        charges: BookingChargeRepository,
        shifts: ShiftRepository,
        bookings: BookingRepository,
        relationships: WorkerRelationshipRepository,
        availability: AvailabilityService,
        organisations: OrganisationRepository,
        agreements: CommercialAgreementRepository,
    ) -> None:
        self._charges = charges
        self._shifts = shifts
        self._bookings = bookings
        self._relationships = relationships
        self._availability = availability
        self._organisations = organisations
        self._agreements = agreements

    def cost_of_coverage(self, venue_id: str, period: str) -> CoverageCost:
        charges = [
            charge for charge in self._charges.list_for_account(venue_id) if charge.period == period
        ]
        totals: dict[str, dict[str, Decimal | int]] = {
            "team": _empty_bucket(),
            "pool": _empty_bucket(),
            "market": _empty_bucket(),
        }
        for charge in charges:
            source = SOURCE_OF_BASIS.get(charge.fee_basis or "outside", "market")
            bucket = totals[source]
            bucket["shifts"] = int(bucket["shifts"]) + 1
            bucket["hours"] += charge.hours
            bucket["wages"] += charge.wages
            bucket["fees"] += charge.fee
        sources = [
            SourceCost(
                source=source,
                shifts=int(bucket["shifts"]),
                hours=money(bucket["hours"]),
                wages=money(bucket["wages"]),
                fees=money(bucket["fees"]),
                cost_per_hour=_per_hour(bucket["wages"] + bucket["fees"], bucket["hours"]),
            )
            for source, bucket in totals.items()
        ]
        hours = money(sum((s.hours for s in sources), ZERO))
        wages = money(sum((s.wages for s in sources), ZERO))
        fees = money(sum((s.fees for s in sources), ZERO))
        return CoverageCost(
            period=period,
            sources=sources,
            hours=hours,
            wages=wages,
            fees=fees,
            cost_per_hour=_per_hour(wages + fees, hours),
        )

    def savings_available(self, venue_id: str, now: datetime, horizon_days: int = 14) -> SavingsAvailable:
        window_end = now + timedelta(days=horizon_days)
        open_shifts = [
            shift
            for shift in self._shifts.list_in_range(venue_id, now, window_end)
            if shift.status == "open" and shift.workers_filled < shift.workers_needed
        ]
        own_members = [
            relationship.worker_id
            for relationship in self._relationships.list_for_venue(venue_id, "active")
            if relationship.relationship_type in EMPLOYED_TYPES
            or relationship.relationship_type == "pool"
        ]
        if not open_shifts or not own_members:
            return SavingsAvailable(opportunities=[], total_fee_avoided=ZERO)
        agreement = agreement_as_of(
            self._agreements, self._organisation_of(venue_id), "GBP", now
        )
        opportunities: list[SavingOpportunity] = []
        total = ZERO
        for shift in open_shifts:
            statuses = self._availability.current_statuses(venue_id, own_members, shift.start_time)
            candidates = [
                worker_id
                for worker_id in own_members
                if statuses[worker_id].status.value == "available"
            ]
            if not candidates:
                continue
            fee_avoided = self._fee_for_market(shift, agreement)
            opportunities.append(
                SavingOpportunity(
                    shift_id=shift.shift_id,
                    role=shift.role,
                    start_time=shift.start_time,
                    available_candidates=len(candidates),
                    fee_avoided=fee_avoided,
                )
            )
            total += fee_avoided
        return SavingsAvailable(opportunities=opportunities, total_fee_avoided=money(total))

    def _fee_for_market(self, shift, agreement) -> Decimal:
        hours = Decimal((shift.end_time - shift.start_time).total_seconds()) / Decimal(3600)
        wages = money(hours * Decimal(shift.pay_rate))
        percent = fee_percent_for(agreement, "outside")
        return money(wages * percent / Decimal(100))

    def _organisation_of(self, venue_id: str) -> str:
        venue = self._organisations.get_venue(venue_id)
        return venue.organisation_id if venue is not None else venue_id


    def what_helps_fill(self, venue_id: str, now: datetime, lookback_days: int = 90) -> FillFactors:
        shifts, filled = self._history(venue_id, now, lookback_days)
        median_pay = _median([Decimal(shift.pay_rate) for shift in shifts])
        lead = _bucketise(shifts, filled, _lead_bucket)
        weekday = _bucketise(shifts, filled, lambda shift: _WEEKDAYS[shift.start_time.weekday()])
        pay = _bucketise(
            shifts, filled, lambda shift: _pay_band(Decimal(shift.pay_rate), median_pay)
        )
        return FillFactors(
            lookback_days=lookback_days,
            by_lead_time=[_fill_bucket(label, s, f) for label, (s, f) in lead.items()],
            by_weekday=[_fill_bucket(label, s, f) for label, (s, f) in weekday.items()],
            by_pay_band=[_fill_bucket(label, s, f) for label, (s, f) in pay.items()],
        )

    def value_of_planning(self, venue_id: str, now: datetime, lookback_days: int = 90) -> PlanningValue:
        shifts, filled = self._history(venue_id, now, lookback_days)
        buckets: dict[str, list] = {}
        for shift in shifts:
            label = _lead_bucket(shift)
            entry = buckets.setdefault(label, [0, 0, []])
            entry[0] += 1
            source = filled.get(shift.shift_id)
            if source is not None:
                entry[1] += 1
                entry[2].append(SOURCE_DEPTH.get(source, 2))
        ordered = [
            PlanningBucket(
                label=label,
                shifts=entry[0],
                filled=entry[1],
                fill_rate=_rate(entry[1], entry[0]),
                average_escalation_depth=(
                    money(Decimal(sum(entry[2])) / Decimal(len(entry[2])))
                    if entry[2] and entry[0] >= MIN_SAMPLE
                    else None
                ),
            )
            for label, entry in buckets.items()
        ]
        return PlanningValue(
            lookback_days=lookback_days,
            by_posting_lead=sorted(ordered, key=lambda bucket: _LEAD_ORDER.index(bucket.label)),
        )

    def _history(self, venue_id: str, now: datetime, lookback_days: int):
        window_start = now - timedelta(days=lookback_days)
        shifts = [
            shift
            for shift in self._shifts.list_in_range(venue_id, window_start, now)
            if shift.status != "cancelled"
        ]
        bookings = self._bookings.list_for_shifts([shift.shift_id for shift in shifts])
        filled: dict[str, str] = {}
        for booking in bookings:
            if booking.state in CHECKED_IN_STATES:
                filled[booking.shift_id] = booking.allocation_source or "market"
        return shifts, filled

def _empty_bucket() -> dict[str, Decimal | int]:
    return {"shifts": 0, "hours": ZERO, "wages": ZERO, "fees": ZERO}


def _per_hour(cost: Decimal, hours: Decimal) -> Decimal | None:
    if hours <= 0:
        return None
    return money(cost / hours)


_WEEKDAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
_LEAD_ORDER = ["<2d", "2-7d", "7-14d", "14d+"]


def _lead_bucket(shift) -> str:
    days = (shift.start_time - (shift.created_at or shift.start_time)).days
    if days < 2:
        return "<2d"
    if days < 7:
        return "2-7d"
    if days < 14:
        return "7-14d"
    return "14d+"


def _pay_band(pay: Decimal, median: Decimal | None) -> str:
    if median is None:
        return "at typical"
    if pay < median:
        return "below typical"
    if pay > median:
        return "above typical"
    return "at typical"


def _bucketise(shifts, filled, key):
    buckets: dict[str, list] = {}
    for shift in shifts:
        entry = buckets.setdefault(key(shift), [0, 0])
        entry[0] += 1
        if shift.shift_id in filled:
            entry[1] += 1
    return {label: (entry[0], entry[1]) for label, entry in buckets.items()}


def _fill_bucket(label: str, shifts: int, filled: int) -> FillBucket:
    return FillBucket(label=label, shifts=shifts, filled=filled, fill_rate=_rate(filled, shifts))


def _rate(filled: int, shifts: int):
    if shifts < MIN_SAMPLE:
        return None
    return money(Decimal(filled) / Decimal(shifts) * Decimal(100))


def _median(values):
    if not values:
        return None
    ordered = sorted(values)
    mid = len(ordered) // 2
    if len(ordered) % 2 == 1:
        return ordered[mid]
    return money((ordered[mid - 1] + ordered[mid]) / Decimal(2))

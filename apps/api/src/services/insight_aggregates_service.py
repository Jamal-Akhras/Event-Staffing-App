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

SOURCE_OF_BASIS = {
    "venue_employed": "team",
    "organisation_employed": "team",
    "venue_pool": "pool",
    "outside": "market",
}
ZERO = Decimal("0.00")


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


def _empty_bucket() -> dict[str, Decimal | int]:
    return {"shifts": 0, "hours": ZERO, "wages": ZERO, "fees": ZERO}


def _per_hour(cost: Decimal, hours: Decimal) -> Decimal | None:
    if hours <= 0:
        return None
    return money(cost / hours)

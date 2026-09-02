from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from apps.api.src.models.worker_profile import WorkerProfile
from apps.api.src.models.worker_relationship import WorkerRelationship
from apps.api.src.repositories.booking_charge_repository import BookingChargeRepository
from apps.api.src.repositories.worker_profile_repository import WorkerProfileRepository
from apps.api.src.repositories.worker_relationship_repository import WorkerRelationshipRepository

ZERO = Decimal("0.00")


@dataclass(frozen=True)
class WorkedTotals:
    shifts: int = 0
    hours: Decimal = ZERO
    wages: Decimal = ZERO
    fees: Decimal = ZERO
    last_worked: datetime | None = None


@dataclass(frozen=True)
class DirectoryEntry:
    relationship: WorkerRelationship
    display_name: str
    role: str
    reliability_score: float
    avatar_url: str | None
    allows_recontact: bool
    totals: WorkedTotals


class PeopleService:
    def __init__(
        self,
        relationships: WorkerRelationshipRepository,
        workers: WorkerProfileRepository,
        charges: BookingChargeRepository,
    ) -> None:
        self._relationships = relationships
        self._workers = workers
        self._charges = charges

    def directory(self, venue_id: str) -> list[DirectoryEntry]:
        relationships = self._relationships.list_for_venue(venue_id)
        if not relationships:
            return []

        profiles = {
            profile.worker_id: profile
            for profile in self._workers.list_by_ids([item.worker_id for item in relationships])
        }
        totals = self._totals_by_worker(venue_id)

        entries = [
            self._entry(relationship, profiles.get(relationship.worker_id), totals)
            for relationship in relationships
        ]
        return sorted(entries, key=lambda entry: entry.display_name.lower())

    def _totals_by_worker(self, venue_id: str) -> dict[str, WorkedTotals]:
        totals: dict[str, WorkedTotals] = {}
        for charge in self._charges.list_for_account(venue_id):
            running = totals.get(charge.worker_id, WorkedTotals())
            last = running.last_worked
            totals[charge.worker_id] = WorkedTotals(
                shifts=running.shifts + 1,
                hours=running.hours + charge.hours,
                wages=running.wages + charge.wages,
                fees=running.fees + charge.fee,
                last_worked=charge.completed_at if last is None or charge.completed_at > last else last,
            )
        return totals

    def _entry(
        self,
        relationship: WorkerRelationship,
        profile: WorkerProfile | None,
        totals: dict[str, WorkedTotals],
    ) -> DirectoryEntry:
        worked = totals.get(relationship.worker_id, WorkedTotals())
        return DirectoryEntry(
            relationship=relationship,
            display_name=profile.display_name if profile and profile.display_name else "Worker",
            role=(profile.role if profile else None) or relationship.default_role or "",
            reliability_score=profile.reliability_score if profile else 0.0,
            avatar_url=getattr(profile, "avatar_url", None),
            allows_recontact=bool(profile.allow_venue_recontact) if profile else False,
            totals=worked,
        )

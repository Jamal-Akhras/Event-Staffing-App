from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from apps.api.src.repositories.organisation_repository import OrganisationRepository
from apps.api.src.repositories.shift_repository import ShiftRepository


@dataclass(frozen=True)
class ShiftSummary:
    shift_id: str
    role: str
    location: str
    pay_rate: Decimal
    currency: str
    start_time: object
    end_time: object
    venue_id: str | None
    venue_name: str | None
    venue_avatar_url: str | None


def summarise_shifts(
    shift_ids: list[str],
    shifts: ShiftRepository,
    venues: OrganisationRepository,
) -> dict[str, ShiftSummary]:
    unique = list(dict.fromkeys(shift_ids))
    if not unique:
        return {}
    found = shifts.list_by_ids(unique)
    venue_cache: dict[str, tuple[str, str | None] | None] = {}
    summaries: dict[str, ShiftSummary] = {}

    for shift in found:
        venue_name = None
        venue_avatar = None
        if shift.account_id:
            if shift.account_id not in venue_cache:
                venue = venues.get_venue(shift.account_id)
                venue_cache[shift.account_id] = (venue.name, venue.avatar_url) if venue else None
            cached = venue_cache[shift.account_id]
            if cached:
                venue_name, venue_avatar = cached
        summaries[shift.shift_id] = ShiftSummary(
            shift_id=shift.shift_id,
            role=shift.role,
            location=shift.location,
            pay_rate=shift.pay_rate,
            currency=shift.currency,
            start_time=shift.start_time,
            end_time=shift.end_time,
            venue_id=shift.account_id,
            venue_name=venue_name,
            venue_avatar_url=venue_avatar,
        )
    return summaries

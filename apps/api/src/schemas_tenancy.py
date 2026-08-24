from __future__ import annotations

from pydantic import BaseModel

from apps.api.src.validation_types import UtcTimestamp


class OrganisationResponse(BaseModel):
    organisation_id: str
    name: str
    country: str
    currency: str
    membership_role: str
    created_at: UtcTimestamp


class VenueSummaryResponse(BaseModel):
    venue_id: str
    organisation_id: str
    name: str
    country: str
    currency: str
    venue_type: str | None
    default_location: str | None
    market_id: str | None

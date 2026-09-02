from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class VenueJoinCode:
    code: str
    venue_id: str
    default_relationship_type: str
    max_redemptions: int
    created_at: datetime
    created_by_user_id: str
    default_role: str | None = None
    expires_at: datetime | None = None
    revoked_at: datetime | None = None


@dataclass(frozen=True)
class VenueJoinCodeRedemption:
    redemption_id: str
    code: str
    venue_id: str
    worker_id: str
    relationship_id: str
    redeemed_at: datetime

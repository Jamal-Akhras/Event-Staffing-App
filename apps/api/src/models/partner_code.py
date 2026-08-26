from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class PartnerCode:
    code: str
    label: str
    waiver_months: int
    shift_cap: int
    max_redemptions: int
    created_at: datetime
    created_by: str
    expires_at: datetime | None = None


@dataclass(frozen=True)
class PartnerCodeRedemption:
    redemption_id: str
    code: str
    account_id: str
    redeemed_at: datetime
    redeemed_by_user_id: str
    fee_waived_until: datetime
    shift_cap: int

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

PLANS = ("classic", "plus", "enterprise")
BOOST_TIERS = ("top1", "top5", "top10")


@dataclass(frozen=True)
class CommercialAgreement:
    agreement_id: str
    organisation_id: str
    plan: str
    monthly_fee_per_site: Decimal
    own_pool_fee_percent: Decimal
    outside_fee_percent: Decimal
    currency: str
    effective_from: datetime
    effective_until: datetime | None
    created_at: datetime
    created_by_user_id: str | None = None

    def __post_init__(self) -> None:
        if self.plan not in PLANS:
            raise ValueError(f"Unknown plan: {self.plan}")


@dataclass(frozen=True)
class SubscriptionCharge:
    subscription_charge_id: str
    organisation_id: str
    venue_id: str
    agreement_id: str
    plan: str
    period: str
    amount: Decimal
    currency: str
    coverage_start: datetime
    coverage_end: datetime
    minted_at: datetime


@dataclass(frozen=True)
class ShiftBoost:
    boost_id: str
    shift_id: str
    venue_id: str
    tier: str
    price: Decimal
    currency: str
    period: str
    status: str
    purchased_by_user_id: str
    purchased_at: datetime

    def __post_init__(self) -> None:
        if self.tier not in BOOST_TIERS:
            raise ValueError(f"Unknown boost tier: {self.tier}")

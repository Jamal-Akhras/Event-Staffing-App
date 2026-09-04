from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from apps.api.src.services.billing_math import money
from apps.api.src.config import get_platform_fee_percent


@dataclass(frozen=True)
class PlanPrice:
    monthly_fee_per_site: Decimal
    own_pool_fee_percent: Decimal
    outside_fee_percent: Decimal


BOOST_PRICES: dict[str, Decimal] = {
    "top1": Decimal("15.00"),
    "top5": Decimal("8.00"),
    "top10": Decimal("4.00"),
}

PLUS_MONTHLY_FEE_PER_SITE = Decimal("25.00")


def plan_price(plan: str) -> PlanPrice:
    fee = money(get_platform_fee_percent())
    if plan == "classic":
        return PlanPrice(Decimal("0.00"), fee, fee)
    if plan == "plus":
        return PlanPrice(PLUS_MONTHLY_FEE_PER_SITE, Decimal("0.00"), fee)
    raise ValueError(
        f"Plan {plan} has no catalogue price; enterprise agreements are set explicitly."
    )


def boost_price(tier: str) -> Decimal:
    price = BOOST_PRICES.get(tier)
    if price is None:
        raise ValueError(f"Unknown boost tier: {tier}")
    return price

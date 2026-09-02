from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta

DEFAULT_POOL_HOURS = 24
DEFAULT_MARKET_LEAD_HOURS = 48


@dataclass(frozen=True)
class EscalationPolicy:
    """How long the venue's own people hold a shift, and the latest it may reach the market.

    `pool_hours` is the length of one private rung: a named worker's hold on an assigned shift, and
    the pool's exclusivity after that. `market_lead_hours` is measured back from the shift start, so
    a late drop reaches the market at once while an early one still gives the pool its window.
    Either may be None, which turns that rung off.
    """

    pool_hours: int | None = DEFAULT_POOL_HOURS
    market_lead_hours: int | None = DEFAULT_MARKET_LEAD_HOURS

    @property
    def offers_pool(self) -> bool:
        return self.pool_hours is not None

    @property
    def reaches_market(self) -> bool:
        return self.market_lead_hours is not None


@dataclass(frozen=True)
class EscalationTimestamps:
    offer_pool_at: datetime | None
    publish_market_at: datetime | None


def policy_from_venue(stored: dict | None) -> EscalationPolicy:
    if not stored:
        return EscalationPolicy()
    return EscalationPolicy(
        pool_hours=_hours(stored, "pool_hours", DEFAULT_POOL_HOURS),
        market_lead_hours=_hours(stored, "market_lead_hours", DEFAULT_MARKET_LEAD_HOURS),
    )


def next_timestamps(
    start_time: datetime,
    from_time: datetime,
    policy: EscalationPolicy,
    assigned: bool,
) -> EscalationTimestamps:
    hold = timedelta(hours=policy.pool_hours or 0)

    offer_pool_at = None
    if policy.offers_pool:
        offer_pool_at = from_time + hold if assigned else from_time

    publish_market_at = None
    if policy.reaches_market:
        previous_rung = offer_pool_at if offer_pool_at is not None else from_time
        window_ends = previous_rung + hold if policy.offers_pool else previous_rung
        deadline = start_time - timedelta(hours=policy.market_lead_hours or 0)
        publish_market_at = max(min(window_ends, deadline), previous_rung)

    return EscalationTimestamps(offer_pool_at=offer_pool_at, publish_market_at=publish_market_at)


def _hours(stored: dict, key: str, fallback: int) -> int | None:
    if key not in stored:
        return fallback
    value = stored[key]
    if value is None:
        return None
    hours = int(value)
    if hours < 0:
        raise ValueError(f"{key} cannot be negative.")
    return hours

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta

DEFAULT_NAMED_OFFER_HOURS = 24
DEFAULT_POOL_HOURS = 24
DEFAULT_MARKET_LEAD_HOURS = 48

RUNG_ORDER = ("assigned", "team", "pool", "market")

_POLICY_KEYS = ("named_offer_hours", "team_hours", "pool_hours", "market_lead_hours")


@dataclass(frozen=True)
class EscalationPolicy:
    named_offer_hours: int | None = DEFAULT_NAMED_OFFER_HOURS
    team_hours: int | None = None
    pool_hours: int | None = DEFAULT_POOL_HOURS
    market_lead_hours: int | None = DEFAULT_MARKET_LEAD_HOURS

    @property
    def offers_team(self) -> bool:
        return self.team_hours is not None

    @property
    def offers_pool(self) -> bool:
        return self.pool_hours is not None

    @property
    def reaches_market(self) -> bool:
        return self.market_lead_hours is not None


@dataclass(frozen=True)
class EscalationTimestamps:
    offer_team_at: datetime | None
    offer_pool_at: datetime | None
    publish_market_at: datetime | None


def policy_from_venue(stored: dict | None) -> EscalationPolicy:
    if not stored:
        return EscalationPolicy()
    missing = [key for key in _POLICY_KEYS if key not in stored]
    if missing:
        raise ValueError(f"The escalation policy is missing {', '.join(missing)}.")
    return EscalationPolicy(**{key: _hours(stored[key], key) for key in _POLICY_KEYS})


def plan_rungs(
    start_time: datetime,
    from_time: datetime,
    policy: EscalationPolicy,
    first_rung: str,
    has_team: bool,
    has_pool: bool,
) -> EscalationTimestamps:
    if first_rung not in RUNG_ORDER:
        raise ValueError(f"Unknown rung '{first_rung}'.")
    first = RUNG_ORDER.index(first_rung)
    cursor = from_time
    team_at: datetime | None = None
    pool_at: datetime | None = None
    market_at: datetime | None = None

    if first_rung == "assigned":
        if policy.named_offer_hours is None:
            return EscalationTimestamps(None, None, None)
        cursor = cursor + timedelta(hours=policy.named_offer_hours)

    if first <= RUNG_ORDER.index("team") and policy.offers_team and has_team:
        team_at = cursor
        cursor = cursor + timedelta(hours=policy.team_hours)

    if first <= RUNG_ORDER.index("pool") and policy.offers_pool and has_pool:
        pool_at = cursor
        cursor = cursor + timedelta(hours=policy.pool_hours)

    if policy.reaches_market:
        deadline = start_time - timedelta(hours=policy.market_lead_hours)
        floor = pool_at or team_at or from_time
        market_at = max(min(cursor, deadline), floor)

    return EscalationTimestamps(
        offer_team_at=team_at, offer_pool_at=pool_at, publish_market_at=market_at
    )


def _hours(value, key: str) -> int | None:
    if value is None:
        return None
    hours = int(value)
    if hours < 0:
        raise ValueError(f"{key} cannot be negative.")
    return hours

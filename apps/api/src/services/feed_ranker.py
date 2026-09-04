from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal

FAMILIARITY_WEIGHT_CAP = Decimal("15")
EXPLORATION_EVERY = 5


@dataclass(frozen=True)
class RankerContext:
    now: datetime
    worker_role: str | None
    market_median_pay: Decimal | None
    familiar_venue_ids: frozenset[str]
    venue_ratings: dict[str, float] = field(default_factory=dict)
    profiling_consent: bool = False


@dataclass(frozen=True)
class RankedShift:
    shift_id: str
    bucket: int
    score: Decimal
    reasons: list[str]
    familiar: bool


def score_shift(shift, bucket: int, ctx: RankerContext) -> RankedShift:
    score = Decimal("0")
    reasons: list[str] = []

    if ctx.market_median_pay and ctx.market_median_pay > 0:
        ratio = Decimal(shift.pay_rate) / ctx.market_median_pay
        if ratio >= Decimal("1.10"):
            score += Decimal("30")
            reasons.append("Higher pay than most nearby")
        elif ratio >= Decimal("1.0"):
            score += Decimal("15")

    lead_days = (shift.start_time - ctx.now).days
    if 0 <= lead_days <= 2:
        score += Decimal("20")
        reasons.append("Starts soon")
    elif lead_days <= 7:
        score += Decimal("10")

    if ctx.worker_role and shift.role.strip().casefold() == ctx.worker_role.strip().casefold():
        score += Decimal("20")
        reasons.append("Matches your role")

    rating = ctx.venue_ratings.get(shift.account_id or "")
    if rating is not None and rating >= 4.5:
        score += Decimal("10")
        reasons.append("Well-rated venue")

    familiar = False
    if ctx.profiling_consent and (shift.account_id or "") in ctx.familiar_venue_ids:
        familiar = True
        score += min(FAMILIARITY_WEIGHT_CAP, Decimal("15"))
        reasons.append("You've worked here before")

    return RankedShift(
        shift_id=shift.shift_id, bucket=bucket, score=score, reasons=reasons, familiar=familiar
    )


def rank_bucket(scored: list[RankedShift]) -> list[RankedShift]:
    ordered = sorted(scored, key=lambda r: (-r.score, r.shift_id))
    if not any(r.familiar for r in ordered):
        return ordered
    unfamiliar = [r for r in ordered if not r.familiar]
    if not unfamiliar:
        return ordered
    result: list[RankedShift] = []
    pool = list(ordered)
    fresh = list(unfamiliar)
    index = 0
    while pool:
        if index % EXPLORATION_EVERY == EXPLORATION_EVERY - 1 and fresh:
            pick = fresh.pop(0)
            pool.remove(pick)
        else:
            pick = pool.pop(0)
            if pick in fresh:
                fresh.remove(pick)
        result.append(pick)
        index += 1
    return result


def build_slate(candidates: list[tuple[object, int]], ctx: RankerContext) -> list[RankedShift]:
    by_bucket: dict[int, list[RankedShift]] = {}
    for shift, bucket in candidates:
        by_bucket.setdefault(bucket, []).append(score_shift(shift, bucket, ctx))
    ordered: list[RankedShift] = []
    for bucket in sorted(by_bucket):
        ordered.extend(rank_bucket(by_bucket[bucket]))
    return ordered

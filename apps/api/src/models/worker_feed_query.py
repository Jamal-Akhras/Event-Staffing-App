from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Literal

from apps.api.src.models.organisation import Venue
from apps.api.src.models.shift import Shift


@dataclass(frozen=True)
class FeedPosition:
    start_time: datetime
    shift_id: str
    bucket: int = 2
    mode: Literal["keyset", "ranked"] = "keyset"
    slate_id: str | None = None
    slate_position: int = 0


@dataclass(frozen=True)
class WorkerFeedQuery:
    worker_id: str
    market_id: str
    timezone: str
    now: datetime
    limit: int
    today_start: datetime
    today_end: datetime
    search: str | None = None
    timing: str = "all"
    minimum_pay: Decimal | None = None
    position: FeedPosition | None = None
    marketplace_enabled: bool = True
    shift_ids: frozenset[str] | None = None


@dataclass(frozen=True)
class WorkerFeedItem:
    shift: Shift
    venue: Venue
    bucket: int = 2
    boosted: bool = False
    boost_tier: str | None = None
    reasons: list[str] = field(default_factory=list)
    slate_position: int | None = None

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from apps.api.src.models.organisation import Venue
from apps.api.src.models.shift import Shift


@dataclass(frozen=True)
class FeedPosition:
    start_time: datetime
    shift_id: str


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


@dataclass(frozen=True)
class WorkerFeedItem:
    shift: Shift
    venue: Venue

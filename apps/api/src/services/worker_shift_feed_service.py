from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, time, timedelta
from decimal import Decimal
from zoneinfo import ZoneInfo

from apps.api.src.datetime_utils import normalize_utc, utc_now
from apps.api.src.models.organisation import Market
from apps.api.src.models.worker_feed_query import FeedPosition, WorkerFeedItem, WorkerFeedQuery
from apps.api.src.repositories.market_repository import MarketRepository
from apps.api.src.repositories.worker_feed_query_repository import WorkerFeedQueryRepository
from apps.api.src.repositories.worker_profile_repository import WorkerProfileRepository
from apps.api.src.services.worker_feed_cursor import (
    decode_feed_cursor,
    encode_feed_cursor,
    filter_fingerprint,
)


class WorkerMarketMissingError(ValueError):
    pass


@dataclass(frozen=True)
class WorkerFeedPage:
    items: list[WorkerFeedItem]
    next_cursor: str | None
    market: Market


class WorkerShiftFeedService:
    def __init__(
        self,
        profiles: WorkerProfileRepository,
        markets: MarketRepository,
        queries: WorkerFeedQueryRepository,
    ) -> None:
        self._profiles = profiles
        self._markets = markets
        self._queries = queries

    def list_page(
        self,
        worker_id: str,
        limit: int,
        cursor: str | None,
        search: str | None,
        timing: str,
        minimum_pay: Decimal | None,
        now: datetime | None = None,
    ) -> WorkerFeedPage:
        profile = self._profiles.get(worker_id)
        if profile is None or profile.market_id is None:
            raise WorkerMarketMissingError("Worker profile has no market.")
        market = self._markets.get(profile.market_id)
        if market is None or not market.is_active:
            raise WorkerMarketMissingError("Worker profile market is unavailable.")
        normalized_search = search.strip() if search and search.strip() else None
        minimum_text = str(minimum_pay) if minimum_pay is not None else None
        fingerprint = filter_fingerprint(normalized_search, timing, minimum_text)
        position = (
            decode_feed_cursor(cursor, worker_id, market.market_id, fingerprint)
            if cursor
            else None
        )
        current_time = normalize_utc(now or utc_now())
        today_start, today_end = _today_bounds(current_time, market.timezone)
        query = WorkerFeedQuery(
            worker_id=worker_id,
            market_id=market.market_id,
            timezone=market.timezone,
            now=current_time,
            limit=limit,
            search=normalized_search,
            timing=timing,
            minimum_pay=minimum_pay,
            position=position,
            today_start=today_start,
            today_end=today_end,
        )
        rows = self._queries.list_page(query)
        items = rows[:limit]
        next_cursor = None
        if len(rows) > limit and items:
            last = items[-1].shift
            next_cursor = encode_feed_cursor(
                FeedPosition(last.start_time, last.shift_id),
                worker_id,
                market.market_id,
                fingerprint,
            )
        return WorkerFeedPage(items=items, next_cursor=next_cursor, market=market)


def _today_bounds(now: datetime, timezone: str) -> tuple[datetime, datetime]:
    zone = ZoneInfo(timezone)
    local_date = now.astimezone(zone).date()
    local_start = datetime.combine(local_date, time.min, tzinfo=zone)
    return normalize_utc(local_start), normalize_utc(local_start + timedelta(days=1))

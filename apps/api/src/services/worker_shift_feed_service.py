from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime, time, timedelta
from decimal import Decimal
from statistics import median
from uuid import uuid4
from zoneinfo import ZoneInfo

from apps.api.src.datetime_utils import normalize_utc, utc_now
from apps.api.src.models.organisation import Market
from apps.api.src.models.worker_feed_query import FeedPosition, WorkerFeedItem, WorkerFeedQuery
from apps.api.src.repositories.market_repository import MarketRepository
from apps.api.src.repositories.worker_feed_query_repository import WorkerFeedQueryRepository
from apps.api.src.repositories.worker_profile_repository import WorkerProfileRepository
from apps.api.src.repositories.worker_relationship_repository import (
    WorkerRelationshipRepository,
)
from apps.api.src.services.feed_ranker import RankerContext, build_slate
from apps.api.src.services.feed_slate_store import (
    FeedSlateStore,
    SlateEntry,
    get_feed_slate_store,
)
from apps.api.src.services.worker_feed_cursor import (
    decode_feed_cursor,
    encode_feed_cursor,
    filter_fingerprint,
)

SLATE_CANDIDATE_CAP = 200


class WorkerMarketMissingError(ValueError):
    pass


@dataclass(frozen=True)
class WorkerFeedPage:
    items: list[WorkerFeedItem]
    next_cursor: str | None
    market: Market
    slate_id: str | None = None
    personalized: bool = False


class WorkerShiftFeedService:
    def __init__(
        self,
        profiles: WorkerProfileRepository,
        markets: MarketRepository,
        queries: WorkerFeedQueryRepository,
        relationships: WorkerRelationshipRepository | None = None,
        slates: FeedSlateStore | None = None,
    ) -> None:
        self._profiles = profiles
        self._markets = markets
        self._queries = queries
        self._relationships = relationships
        self._slates = slates

    def list_page(
        self,
        worker_id: str,
        limit: int,
        cursor: str | None,
        search: str | None,
        timing: str,
        minimum_pay: Decimal | None,
        now: datetime | None = None,
        rank: bool = False,
        profiling_consent: bool = False,
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
        expected_mode = "ranked" if rank else "keyset"
        if position is not None and position.mode != expected_mode:
            position = None
        current_time = normalize_utc(now or utc_now())
        today_start, today_end = _today_bounds(current_time, market.timezone)

        def _query(
            query_limit: int,
            query_position: FeedPosition | None,
            shift_ids: frozenset[str] | None = None,
        ) -> WorkerFeedQuery:
            return WorkerFeedQuery(
                worker_id=worker_id,
                market_id=market.market_id,
                timezone=market.timezone,
                now=current_time,
                limit=query_limit,
                search=normalized_search,
                timing=timing,
                minimum_pay=minimum_pay,
                position=query_position,
                today_start=today_start,
                today_end=today_end,
                marketplace_enabled=profile.marketplace_enabled,
                shift_ids=shift_ids,
            )

        if rank:
            return self._ranked_page(
                worker_id=worker_id,
                profile=profile,
                market=market,
                limit=limit,
                position=position,
                fingerprint=fingerprint,
                current_time=current_time,
                build_query=_query,
                profiling_consent=profiling_consent,
            )

        rows = self._queries.list_page(_query(limit, position))
        items = rows[:limit]
        next_cursor = None
        if len(rows) > limit and items:
            last = items[-1]
            next_cursor = encode_feed_cursor(
                FeedPosition(last.shift.start_time, last.shift.shift_id, last.bucket),
                worker_id,
                market.market_id,
                fingerprint,
            )
        return WorkerFeedPage(
            items=_promote_boosts(items, limit), next_cursor=next_cursor, market=market
        )

    def _ranked_page(
        self,
        worker_id: str,
        profile,
        market: Market,
        limit: int,
        position: FeedPosition | None,
        fingerprint: str,
        current_time: datetime,
        build_query,
        profiling_consent: bool,
    ) -> WorkerFeedPage:
        store = self._slates or get_feed_slate_store()

        order: list[SlateEntry] | None = None
        slate_id = position.slate_id if position else None
        start = position.slate_position if position else 0
        if slate_id is not None:
            order = store.get(worker_id, slate_id)
        if order is None:
            candidates = self._queries.list_page(build_query(SLATE_CANDIDATE_CAP, None))[
                :SLATE_CANDIDATE_CAP
            ]
            familiar = self._familiar_venue_ids(worker_id, profiling_consent)
            ctx = RankerContext(
                now=current_time,
                worker_role=profile.role,
                market_median_pay=_median_pay(candidates),
                familiar_venue_ids=familiar,
                venue_ratings={},
                profiling_consent=profiling_consent,
            )
            ranked = build_slate(
                [(item.shift, item.bucket) for item in candidates], ctx
            )
            order = [SlateEntry(r.shift_id, r.reasons) for r in ranked]
            slate_id = uuid4().hex
            store.save(worker_id, slate_id, order)
            start = 0
        else:
            remaining_ids = frozenset(entry.shift_id for entry in order[start:])
            candidates = (
                self._queries.list_page(
                    build_query(len(remaining_ids), None, remaining_ids)
                )[: len(remaining_ids)]
                if remaining_ids
                else []
            )
        by_id = {item.shift.shift_id: item for item in candidates}

        page_items: list[WorkerFeedItem] = []
        consumed = 0
        for entry in order[start:]:
            consumed += 1
            item = by_id.get(entry.shift_id)
            if item is None:
                continue
            page_items.append(replace(item, reasons=entry.reasons))
            if len(page_items) >= limit:
                break

        next_position = start + consumed
        next_cursor = None
        if next_position < len(order):
            next_cursor = encode_feed_cursor(
                FeedPosition(
                    current_time,
                    "",
                    2,
                    mode="ranked",
                    slate_id=slate_id,
                    slate_position=next_position,
                ),
                worker_id,
                market.market_id,
                fingerprint,
            )
        presented_items = [
            replace(item, slate_position=start + offset)
            for offset, item in enumerate(_promote_boosts(page_items, limit))
        ]
        return WorkerFeedPage(
            items=presented_items,
            next_cursor=next_cursor,
            market=market,
            slate_id=slate_id,
            personalized=True,
        )

    def _familiar_venue_ids(self, worker_id: str, profiling_consent: bool) -> frozenset[str]:
        if not profiling_consent or self._relationships is None:
            return frozenset()
        return frozenset(
            relationship.venue_id
            for relationship in self._relationships.list_for_worker(worker_id)
        )


_TIER_RANK = {"top1": 0, "top5": 1, "top10": 2}
BOOST_PAGE_FRACTION = 5


def _median_pay(items) -> Decimal | None:
    rates = [Decimal(item.shift.pay_rate) for item in items if item.bucket == 2]
    if not rates:
        rates = [Decimal(item.shift.pay_rate) for item in items]
    if not rates:
        return None
    return Decimal(median(rates))


def _promote_boosts(items, limit):
    market = [item for item in items if item.bucket == 2]
    if not any(item.boost_tier for item in market):
        return items
    non_market = [item for item in items if item.bucket != 2]
    cap = max(1, limit // BOOST_PAGE_FRACTION)
    boosted = sorted(
        (item for item in market if item.boost_tier),
        key=lambda item: (
            _TIER_RANK.get(item.boost_tier, 9),
            item.shift.start_time,
            item.shift.shift_id,
        ),
    )
    promoted = boosted[:cap]
    promoted_ids = {item.shift.shift_id for item in promoted}
    remaining = [item for item in market if item.shift.shift_id not in promoted_ids]
    return non_market + promoted + remaining


def _today_bounds(now: datetime, timezone: str) -> tuple[datetime, datetime]:
    zone = ZoneInfo(timezone)
    local_date = now.astimezone(zone).date()
    local_start = datetime.combine(local_date, time.min, tzinfo=zone)
    return normalize_utc(local_start), normalize_utc(local_start + timedelta(days=1))

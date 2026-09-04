from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

from apps.api.src.models.shift import Shift
from apps.api.src.services.feed_ranker import (
    RankerContext,
    build_slate,
    score_shift,
)
from apps.api.src.services.feed_slate_store import (
    InMemoryFeedSlateStore,
    SlateEntry,
)

NOW = datetime(2030, 6, 3, 9, 0, tzinfo=UTC)


def _shift(shift_id: str, venue: str, role: str, rate: str, days_ahead: int = 5) -> Shift:
    start = NOW + timedelta(days=days_ahead)
    return Shift(
        shift_id=shift_id, operator_id="op", account_id=venue, role=role, location="Bar",
        start_time=start, end_time=start + timedelta(hours=5), pay_rate=Decimal(rate), notes=None,
        status="open", created_at=NOW, workers_needed=1, workers_filled=0, origin="market",
    )


def _ctx(**overrides) -> RankerContext:
    base = dict(
        now=NOW, worker_role="Bartender", market_median_pay=Decimal("14.00"),
        familiar_venue_ids=frozenset(), venue_ratings={}, profiling_consent=False,
    )
    base.update(overrides)
    return RankerContext(**base)


def test_objective_signals_score_and_explain():
    high = score_shift(_shift("a", "v1", "Bartender", "16.00", days_ahead=1), 2, _ctx())
    assert "Higher pay than most nearby" in high.reasons
    assert "Starts soon" in high.reasons
    assert "Matches your role" in high.reasons
    assert high.score > 0
    low = score_shift(_shift("b", "v2", "Chef", "13.00", days_ahead=20), 2, _ctx())
    assert low.reasons == []
    assert high.score > low.score


def test_familiarity_is_dropped_without_profiling_consent():
    shift = _shift("a", "v1", "Server", "14.00")
    ctx = _ctx(worker_role="Server", familiar_venue_ids=frozenset({"v1"}), profiling_consent=False)
    result = score_shift(shift, 2, ctx)
    assert result.familiar is False
    assert "You've worked here before" not in result.reasons

    with_consent = score_shift(shift, 2, _ctx(
        worker_role="Server", familiar_venue_ids=frozenset({"v1"}), profiling_consent=True
    ))
    assert with_consent.familiar is True
    assert "You've worked here before" in with_consent.reasons
    assert with_consent.score > result.score


def test_l5_a_better_objective_new_shift_still_ranks_above_a_familiar_one():
    familiar = _shift("familiar", "v1", "Chef", "13.00", days_ahead=20)
    fresh = _shift("fresh", "v2", "Bartender", "16.00", days_ahead=1)
    ctx = _ctx(worker_role="Bartender", familiar_venue_ids=frozenset({"v1"}), profiling_consent=True)
    slate = build_slate([(familiar, 2), (fresh, 2)], ctx)
    assert slate[0].shift_id == "fresh"


def test_l5_exploration_surfaces_unfamiliar_shifts_among_many_familiar():
    ctx = _ctx(
        worker_role="Bartender",
        familiar_venue_ids=frozenset({f"fam{i}" for i in range(9)}),
        profiling_consent=True,
    )
    candidates = [(_shift(f"f{i}", f"fam{i}", "Bartender", "14.00", days_ahead=5), 2) for i in range(9)]
    candidates.append((_shift("new", "newvenue", "Bartender", "14.00", days_ahead=5), 2))
    slate = build_slate(candidates, ctx)
    top_five = [r.shift_id for r in slate[:5]]
    assert "new" in top_five  # exploration lifts the unfamiliar shift into the first page


def test_slate_store_round_trips_and_expires():
    store = InMemoryFeedSlateStore()
    entries = [SlateEntry("s1", ["Starts soon"]), SlateEntry("s2", [])]
    store.save("worker-1", "slate-1", entries)
    loaded = store.get("worker-1", "slate-1")
    assert [e.shift_id for e in loaded] == ["s1", "s2"]
    assert loaded[0].reasons == ["Starts soon"]
    assert store.get("worker-2", "slate-1") is None
    assert store.get("worker-1", "missing") is None

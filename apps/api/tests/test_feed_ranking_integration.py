from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient

from apps.api.src import main
from apps.api.src.models.account import Account
from apps.api.src.models.event import EventQuery
from apps.api.src.models.organisation import Venue
from apps.api.src.models.shift import Shift
from apps.api.src.models.worker_profile import WorkerProfile
from apps.api.src.models.worker_relationship import WorkerRelationship
from apps.api.src.repository_dependencies import (
    get_account_repo,
    get_event_repo,
    get_organisation_repo,
    get_shift_repo,
    get_worker_profile_repo,
)
from apps.api.src.repository_dependencies_workforce import shared_worker_relationship_repository
from apps.api.src.services.feed_slate_store import get_feed_slate_store

NOW = datetime.now(UTC)
START = NOW + timedelta(days=5)
WORKER = {"X-Actor-Role": "worker", "X-Actor-Id": "worker-1"}


@pytest.fixture(autouse=True)
def clear_state():
    shared_worker_relationship_repository().clear()
    yield
    shared_worker_relationship_repository().clear()


@pytest.fixture()
def ranked_client(in_memory_repos, monkeypatch):
    monkeypatch.setenv("FEED_RANKING_ENABLED", "1")
    for venue_id, name in (("venue-open", "The Open Arms"), ("venue-fam", "The Regulars")):
        in_memory_repos[get_account_repo].save(
            Account(
                account_id=venue_id, name=name, country="GB", currency="GBP",
                created_at=NOW, market_id="bath-gb",
            )
        )
        in_memory_repos[get_organisation_repo].save_venue(
            Venue(
                venue_id=venue_id, organisation_id="org-1", name=name, country="GB",
                currency="GBP", created_at=NOW, market_id="bath-gb",
            )
        )
    in_memory_repos[get_worker_profile_repo].save(
        WorkerProfile(
            worker_id="worker-1", display_name="Alex", role="Bartender", city="Bath",
            experience_years=1, reliability_score=1.0, badges=[], bio=None, languages=["en"],
            email=None, phone=None, address=None, emergency_contact=None, pay_rate=None,
            notes=None, updated_at=NOW, market_id="bath-gb",
        )
    )
    shared_worker_relationship_repository().save(
        WorkerRelationship(
            relationship_id="rel-fam", venue_id="venue-fam", worker_id="worker-1",
            relationship_type="pool", status="active", created_at=NOW, updated_at=NOW,
        )
    )

    def shift(shift_id, venue_id, origin, rate, hour_offset):
        in_memory_repos[get_shift_repo].save(
            Shift(
                shift_id=shift_id, operator_id="operator-1", account_id=venue_id,
                role="Bartender", location="Main bar",
                start_time=START + timedelta(hours=hour_offset),
                end_time=START + timedelta(hours=hour_offset + 5),
                pay_rate=Decimal(rate), notes=None, status="open", created_at=NOW,
                workers_needed=1, workers_filled=0, origin=origin,
            )
        )

    shift("m-low", "venue-open", "market", "13.00", 0)
    shift("m-high", "venue-open", "market", "18.00", 1)
    shift("m-mid", "venue-open", "market", "15.00", 2)
    shift("m-fam", "venue-fam", "market", "14.00", 3)
    shift("s-pool", "venue-fam", "pool", "14.00", 4)
    return TestClient(main.app)


def _page(client, limit, cursor=None):
    url = f"/workers/me/feed?limit={limit}"
    if cursor:
        url += f"&cursor={cursor}"
    return client.get(url, headers=WORKER).json()


def _market_order(items):
    return [i["shift_id"] for i in items if not i["shift_id"].startswith("s-")]


def test_ranking_orders_the_market_by_score_and_keeps_the_ladder(ranked_client):
    body = _page(ranked_client, 20)
    assert body["personalized"] is True
    order = [i["shift_id"] for i in body["items"]]
    assert order[0] == "s-pool"
    assert _market_order(body["items"]) == ["m-high", "m-mid", "m-fam", "m-low"]
    top_market = next(i for i in body["items"] if i["shift_id"] == "m-high")
    assert "Higher pay than most nearby" in top_market["reasons"]
    assert "Matches your role" in top_market["reasons"]


def test_familiarity_reason_is_gated_on_profiling_consent(ranked_client):
    without = _page(ranked_client, 20)
    fam_without = next(i for i in without["items"] if i["shift_id"] == "m-fam")
    assert "You've worked here before" not in fam_without["reasons"]

    granted = ranked_client.put(
        "/me/consents/profiling", json={"granted": True}, headers=WORKER
    )
    assert granted.status_code == 200, granted.text

    body = _page(ranked_client, 20)
    fam_with = next(i for i in body["items"] if i["shift_id"] == "m-fam")
    assert "You've worked here before" in fam_with["reasons"]
    order = _market_order(body["items"])
    assert order.index("m-fam") < order.index("m-mid")


def test_ranked_pagination_is_stable_and_complete(ranked_client):
    full = _market_order(_page(ranked_client, 50)["items"])

    seen: list[str] = []
    cursor = None
    for _ in range(10):
        body = _page(ranked_client, 2, cursor)
        seen.extend(i["shift_id"] for i in body["items"])
        cursor = body["next_cursor"]
        if not cursor:
            break
    assert cursor is None
    assert len(seen) == len(set(seen))
    assert [s for s in seen if not s.startswith("s-")] == full


def test_the_slate_re_filters_out_a_shift_the_worker_passes(ranked_client):
    first = _page(ranked_client, 1)
    assert [i["shift_id"] for i in first["items"]] == ["s-pool"]
    cursor = first["next_cursor"]

    passed = ranked_client.put(
        "/workers/worker-1/feed-state/m-high",
        json={"action": "passed"},
        headers=WORKER,
    )
    assert passed.status_code == 200, passed.text

    seen: list[str] = []
    for _ in range(10):
        body = _page(ranked_client, 1, cursor)
        seen.extend(i["shift_id"] for i in body["items"])
        cursor = body["next_cursor"]
        if not cursor:
            break
    assert "m-high" not in seen
    assert seen == ["m-mid", "m-fam", "m-low"]


def test_an_entirely_filtered_remainder_is_terminal(ranked_client):
    first = _page(ranked_client, 1)
    for shift_id in ("m-high", "m-mid", "m-fam", "m-low"):
        response = ranked_client.put(
            f"/workers/worker-1/feed-state/{shift_id}",
            json={"action": "passed"},
            headers=WORKER,
        )
        assert response.status_code == 200, response.text

    terminal = _page(ranked_client, 1, first["next_cursor"])
    assert terminal["items"] == []
    assert terminal["next_cursor"] is None


def test_live_refilter_keeps_original_slate_items_when_new_candidates_arrive(
    ranked_client, in_memory_repos
):
    shifts = in_memory_repos[get_shift_repo]
    for index in range(195):
        start_time = START + timedelta(days=10, minutes=index)
        shifts.save(
            Shift(
                shift_id=f"extra-{index:03d}", operator_id="operator-1",
                account_id="venue-open", role="Bartender", location="Main bar",
                start_time=start_time, end_time=start_time + timedelta(hours=5),
                pay_rate=Decimal("15.00"), notes=None, status="open", created_at=NOW,
                workers_needed=1, workers_filled=0, origin="market",
            )
        )

    first = _page(ranked_client, 1)
    slate = get_feed_slate_store().get("worker-1", first["slate_id"])
    assert slate is not None and len(slate) == 200
    original_ids = {entry.shift_id for entry in slate}

    shifts.save(
        Shift(
            shift_id="s-new", operator_id="operator-1", account_id="venue-fam",
            role="Bartender", location="Main bar", start_time=START + timedelta(minutes=1),
            end_time=START + timedelta(hours=5), pay_rate=Decimal("15.00"), notes=None,
            status="open", created_at=NOW, workers_needed=1, workers_filled=0, origin="pool",
        )
    )

    seen = {item["shift_id"] for item in first["items"]}
    cursor = first["next_cursor"]
    for _ in range(10):
        if cursor is None:
            break
        page = _page(ranked_client, 50, cursor)
        seen.update(item["shift_id"] for item in page["items"])
        cursor = page["next_cursor"]
    assert cursor is None
    assert seen == original_ids


def test_ranked_served_positions_do_not_restart_on_each_page(
    ranked_client, in_memory_repos
):
    first = _page(ranked_client, 2)
    second = _page(ranked_client, 2, first["next_cursor"])
    assert len(first["items"]) == len(second["items"]) == 2

    events = in_memory_repos[get_event_repo].query(
        EventQuery(name="shift.served", slate_id=first["slate_id"], limit=20)
    )
    assert sorted(event.position for event in events) == [0, 1, 2, 3]


def test_ranked_cursor_restarts_cleanly_if_ranking_is_disabled(ranked_client, monkeypatch):
    first = _page(ranked_client, 1)
    monkeypatch.setenv("FEED_RANKING_ENABLED", "0")

    restarted = _page(ranked_client, 1, first["next_cursor"])
    assert restarted["items"][0]["shift_id"] == "s-pool"


def test_ranking_stays_off_without_the_flag(in_memory_repos):
    in_memory_repos[get_account_repo].save(
        Account(
            account_id="venue-open", name="The Open Arms", country="GB", currency="GBP",
            created_at=NOW, market_id="bath-gb",
        )
    )
    in_memory_repos[get_organisation_repo].save_venue(
        Venue(
            venue_id="venue-open", organisation_id="org-1", name="The Open Arms",
            country="GB", currency="GBP", created_at=NOW, market_id="bath-gb",
        )
    )
    in_memory_repos[get_worker_profile_repo].save(
        WorkerProfile(
            worker_id="worker-1", display_name="Alex", role="Bartender", city="Bath",
            experience_years=1, reliability_score=1.0, badges=[], bio=None, languages=["en"],
            email=None, phone=None, address=None, emergency_contact=None, pay_rate=None,
            notes=None, updated_at=NOW, market_id="bath-gb",
        )
    )
    in_memory_repos[get_shift_repo].save(
        Shift(
            shift_id="m-high", operator_id="operator-1", account_id="venue-open",
            role="Bartender", location="Main bar", start_time=START,
            end_time=START + timedelta(hours=5), pay_rate=Decimal("18.00"), notes=None,
            status="open", created_at=NOW, workers_needed=1, workers_filled=0, origin="market",
        )
    )
    body = TestClient(main.app).get("/workers/me/feed?limit=20", headers=WORKER).json()
    assert body["personalized"] is False
    assert body["items"][0]["reasons"] == []

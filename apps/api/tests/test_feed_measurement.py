from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient

from apps.api.src import main
from apps.api.src.repository_dependencies import shared_event_repository

WORKER = {"X-Actor-Role": "worker", "X-Actor-Id": "worker-1", "X-Client": "mobile", "X-Session-Id": "feed-session"}
SYSTEM = {"X-Actor-Role": "system", "X-Actor-Id": "system"}


def _events(client, name):
    page = client.get(f"/system/events?name={name}&limit=50", headers=SYSTEM)
    assert page.status_code == 200
    return page.json()["events"]


@pytest.fixture(autouse=True)
def clear_events():
    shared_event_repository().clear()
    yield
    shared_event_repository().clear()


def test_client_events_carry_slate_position_and_version():
    client = TestClient(main.app)
    response = client.post(
        "/events",
        json={
            "events": [
                {
                    "name": "shift.viewed",
                    "subject_type": "shift",
                    "subject_id": "shift-7",
                    "slate_id": "slate-abc",
                    "position": 4,
                    "event_version": 2,
                },
                {
                    "name": "shift.detail_closed",
                    "subject_type": "shift",
                    "subject_id": "shift-7",
                    "slate_id": "slate-abc",
                    "position": 4,
                    "dwell_ms": 8200,
                },
            ]
        },
        headers=WORKER,
    )
    assert response.status_code == 202

    viewed = _events(client, "shift.viewed")[0]
    assert viewed["slate_id"] == "slate-abc"
    assert viewed["position"] == 4
    assert viewed["event_version"] == 2

    closed = _events(client, "shift.detail_closed")[0]
    assert closed["dwell_ms"] == 8200
    assert closed["event_version"] == 1


def test_a_slate_can_be_reassembled_from_its_id():
    client = TestClient(main.app)
    client.post(
        "/events",
        json={
            "events": [
                {"name": "shift.viewed", "subject_id": "shift-a", "slate_id": "slate-1", "position": 0},
                {"name": "shift.viewed", "subject_id": "shift-b", "slate_id": "slate-1", "position": 1},
                {"name": "shift.viewed", "subject_id": "shift-c", "slate_id": "slate-2", "position": 0},
            ]
        },
        headers=WORKER,
    )
    page = client.get("/system/events?slate_id=slate-1&limit=50", headers=SYSTEM).json()
    assert {event["subject_id"] for event in page["events"]} == {"shift-a", "shift-b"}
    assert sorted(event["position"] for event in page["events"]) == [0, 1]


def test_position_and_dwell_are_range_checked():
    client = TestClient(main.app)
    bad_position = {"events": [{"name": "shift.viewed", "position": -1}]}
    bad_dwell = {"events": [{"name": "shift.viewed", "dwell_ms": -5}]}
    assert client.post("/events", json=bad_position, headers=WORKER).status_code == 422
    assert client.post("/events", json=bad_dwell, headers=WORKER).status_code == 422


def test_the_feed_records_what_it_served():
    from decimal import Decimal

    from apps.api.src.deps import get_worker_shift_feed_service
    from apps.api.src.models.organisation import Market, Venue
    from apps.api.src.models.shift import Shift
    from apps.api.src.models.worker_feed_query import WorkerFeedItem
    from apps.api.src.services.worker_shift_feed_service import WorkerFeedPage

    created = datetime(2030, 5, 1, tzinfo=UTC)
    market = Market(
        market_id="bath-gb",
        name="Bath",
        country="GB",
        currency="GBP",
        timezone="Europe/London",
        high_pay_threshold=Decimal("15.00"),
        is_active=True,
        created_at=created,
    )
    venue = Venue(
        venue_id="venue-1",
        organisation_id="org-1",
        name="Temp Venue",
        country="GB",
        currency="GBP",
        created_at=created,
    )
    items = [
        WorkerFeedItem(
            shift=Shift(
                shift_id=f"shift-{index}",
                operator_id="operator-1",
                account_id="venue-1",
                role="Bartender",
                location="Main bar",
                start_time=created,
                end_time=created,
                pay_rate=Decimal("14.50"),
                notes=None,
                status="open",
                created_at=created,
                workers_needed=1,
                workers_filled=0,
            ),
            venue=venue,
        )
        for index in range(3)
    ]

    class _Feed:
        def list_page(self, **kwargs):
            return WorkerFeedPage(items=items, next_cursor=None, market=market)

    main.app.dependency_overrides[get_worker_shift_feed_service] = lambda: _Feed()
    client = TestClient(main.app)
    response = client.get("/workers/me/feed", headers=WORKER)
    assert response.status_code == 200

    slate_id = response.json()["slate_id"]
    assert slate_id

    served = _events(client, "shift.served")
    assert len(served) == 3
    assert {event["slate_id"] for event in served} == {slate_id}
    assert sorted(event["position"] for event in served) == [0, 1, 2]
    assert {event["subject_id"] for event in served} == {"shift-0", "shift-1", "shift-2"}
    assert all(event["venue_id"] == "venue-1" for event in served)

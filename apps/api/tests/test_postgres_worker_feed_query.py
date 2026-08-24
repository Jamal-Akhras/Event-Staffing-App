from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient

from apps.api.src import main
from apps.api.src.db.models import ApplicationModel, ShiftModel, WorkerFeedStateModel
from apps.api.src.db.tenancy_models import MarketModel, OrganisationModel, VenueModel

pytestmark = pytest.mark.postgres

BASE_NOW = datetime(2030, 1, 4, 12, 0, tzinfo=UTC)
PASSWORD = "worker-feed-pass-1"
INVITE_CODE = "worker-feed-invite"


@pytest.fixture()
def client(monkeypatch):
    monkeypatch.setenv("OPERATOR_INVITE_CODES", INVITE_CODE)
    monkeypatch.setattr(
        "apps.api.src.services.worker_shift_feed_service.utc_now",
        lambda: BASE_NOW,
    )
    return TestClient(main.app)


def _session():
    from apps.api.src.db.database import SessionLocal

    return SessionLocal()


def _register_worker(client: TestClient, suffix: str = "one") -> tuple[str, dict[str, str]]:
    response = client.post(
        "/auth/register",
        json={"email": f"feed-{suffix}@example.com", "password": PASSWORD},
    )
    assert response.status_code == 200, response.text
    payload = response.json()
    return payload["worker_profile_id"], {
        "Authorization": f"Bearer {payload['access_token']}"
    }


def _select_bath(client: TestClient, worker_id: str, headers: dict[str, str]) -> None:
    response = client.put(
        f"/workers/{worker_id}",
        headers=headers,
        json={
            "display_name": "Alex",
            "role": "Bartender",
            "city": "Bath",
            "experience_years": 2,
            "languages": ["English"],
            "market_id": "bath-gb",
            "now": BASE_NOW.isoformat(),
        },
    )
    assert response.status_code == 200, response.text
    assert response.json()["market_id"] == "bath-gb"


def _seed_venues() -> None:
    with _session() as session:
        session.add(
            MarketModel(
                market_id="bristol-gb",
                name="Bristol",
                country="GB",
                currency="GBP",
                timezone="Europe/London",
                high_pay_threshold=Decimal("16.00"),
                is_active=True,
                created_at=BASE_NOW,
            )
        )
        for suffix, market_id, name in (
            ("bath", "bath-gb", "Abbey House"),
            ("bristol", "bristol-gb", "Harbourside Hotel"),
        ):
            session.add(
                OrganisationModel(
                    organisation_id=f"org-{suffix}",
                    name=f"{name} Group",
                    country="GB",
                    currency="GBP",
                    created_at=BASE_NOW,
                )
            )
            session.add(
                VenueModel(
                    venue_id=f"venue-{suffix}",
                    organisation_id=f"org-{suffix}",
                    market_id=market_id,
                    name=name,
                    country="GB",
                    currency="GBP",
                    created_at=BASE_NOW,
                    avatar_url=f"https://example.com/{suffix}.png",
                )
            )
        session.commit()


def _shift(
    shift_id: str,
    start: datetime,
    *,
    venue_id: str = "venue-bath",
    role: str = "Bartender",
    pay: str = "14.50",
    status: str = "open",
    needed: int = 1,
    filled: int = 0,
) -> ShiftModel:
    return ShiftModel(
        shift_id=shift_id,
        operator_id=f"operator-{venue_id}",
        venue_id=venue_id,
        role=role,
        location="Bath city centre" if venue_id == "venue-bath" else "Bristol",
        start_time=start,
        end_time=start + timedelta(hours=4),
        pay_rate=Decimal(pay),
        status=status,
        created_at=BASE_NOW,
        workers_needed=needed,
        workers_filled=filled,
        currency="GBP",
    )


def test_market_contract_and_profile_assignment(client: TestClient):
    markets = client.get("/markets")
    assert markets.status_code == 200
    assert markets.json() == [
        {
            "market_id": "bath-gb",
            "name": "Bath",
            "country": "GB",
            "currency": "GBP",
            "timezone": "Europe/London",
            "high_pay_threshold": "15.00",
        }
    ]

    worker_id, worker_headers = _register_worker(client)
    missing_market = client.get("/workers/me/feed", headers=worker_headers)
    assert missing_market.status_code == 409
    assert missing_market.json()["detail"] == "Worker profile has no market."
    _select_bath(client, worker_id, worker_headers)
    feed = client.get("/workers/me/feed", headers=worker_headers)
    assert feed.status_code == 200, feed.text
    assert feed.json()["market"]["market_id"] == "bath-gb"

    operator = client.post(
        "/auth/register/operator",
        json={
            "email": "feed-operator@example.com",
            "password": PASSWORD,
            "venue_name": "The Feed Tavern",
            "country": "GB",
            "market_id": "bath-gb",
            "invite_code": INVITE_CODE,
        },
    )
    assert operator.status_code == 200, operator.text
    venue = client.get(
        "/venues/me",
        headers={"Authorization": f"Bearer {operator.json()['access_token']}"},
    )
    assert venue.status_code == 200, venue.text
    assert venue.json()["market_id"] == "bath-gb"


def test_feed_filters_in_postgres_and_excludes_ineligible_rows(client: TestClient):
    worker_id, headers = _register_worker(client, "filters")
    _select_bath(client, worker_id, headers)
    _seed_venues()
    today = BASE_NOW + timedelta(hours=2)
    weekend = BASE_NOW + timedelta(days=1)
    with _session() as session:
        session.add_all(
            [
                _shift("eligible-today", today),
                _shift("eligible-weekend", weekend, role="Server", pay="16.00"),
                _shift("other-market", today, venue_id="venue-bristol"),
                _shift("filled", today + timedelta(hours=1), needed=1, filled=1),
                _shift("closed", today + timedelta(hours=2), status="closed"),
                _shift("past", BASE_NOW - timedelta(hours=2)),
                _shift("passed", weekend + timedelta(hours=1)),
                _shift("applied", weekend + timedelta(hours=2)),
            ]
        )
        session.flush()
        session.add(
            WorkerFeedStateModel(
                worker_id=worker_id,
                shift_id="passed",
                action="passed",
                created_at=BASE_NOW,
                updated_at=BASE_NOW,
            )
        )
        session.add(
            ApplicationModel(
                application_id="feed-application",
                shift_id="applied",
                worker_id=worker_id,
                operator_id="operator-venue-bath",
                start_time=weekend + timedelta(hours=2),
                end_time=weekend + timedelta(hours=6),
                status="applied",
                created_at=BASE_NOW,
            )
        )
        session.commit()

    feed = client.get("/workers/me/feed", headers=headers)
    assert feed.status_code == 200, feed.text
    assert [item["shift_id"] for item in feed.json()["items"]] == [
        "eligible-today",
        "eligible-weekend",
    ]
    assert feed.json()["items"][0]["venue"] == {
        "venue_id": "venue-bath",
        "name": "Abbey House",
        "avatar_url": "https://example.com/bath.png",
    }
    assert [item["shift_id"] for item in client.get(
        "/workers/me/feed?timing=today", headers=headers
    ).json()["items"]] == ["eligible-today"]
    assert [item["shift_id"] for item in client.get(
        "/workers/me/feed?timing=weekend", headers=headers
    ).json()["items"]] == ["eligible-weekend"]
    assert [item["shift_id"] for item in client.get(
        "/workers/me/feed?minimum_pay=15", headers=headers
    ).json()["items"]] == ["eligible-weekend"]
    assert len(client.get("/workers/me/feed?query=abbey", headers=headers).json()["items"]) == 2
    assert client.get("/workers/me/feed?query=%25", headers=headers).json()["items"] == []


def test_keyset_cursor_is_stable_signed_and_filter_bound(client: TestClient):
    worker_id, headers = _register_worker(client, "cursor")
    _select_bath(client, worker_id, headers)
    _seed_venues()
    start = BASE_NOW + timedelta(hours=3)
    with _session() as session:
        session.add_all(
            [
                _shift("cursor-a", start),
                _shift("cursor-b", start),
                _shift("cursor-c", start + timedelta(hours=1)),
            ]
        )
        session.commit()

    first = client.get("/workers/me/feed?limit=2", headers=headers)
    assert first.status_code == 200, first.text
    first_body = first.json()
    assert [item["shift_id"] for item in first_body["items"]] == ["cursor-a", "cursor-b"]
    assert first_body["next_cursor"]

    second = client.get(
        "/workers/me/feed",
        params={"limit": 2, "cursor": first_body["next_cursor"]},
        headers=headers,
    )
    assert second.status_code == 200, second.text
    assert [item["shift_id"] for item in second.json()["items"]] == ["cursor-c"]
    assert second.json()["next_cursor"] is None

    tampered = client.get(
        "/workers/me/feed",
        params={"cursor": f"{first_body['next_cursor']}x"},
        headers=headers,
    )
    assert tampered.status_code == 422
    mismatched = client.get(
        "/workers/me/feed",
        params={"cursor": first_body["next_cursor"], "query": "bar"},
        headers=headers,
    )
    assert mismatched.status_code == 422

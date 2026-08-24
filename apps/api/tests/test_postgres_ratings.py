from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient

from apps.api.src.db.models import BookingModel, RatingModel, ShiftModel, WorkerProfileModel
from apps.api.src.db.tenancy_models import OrganisationModel, VenueModel
from apps.api.src.main import app
from packages.domain.src.booking_state import BookingState

pytestmark = pytest.mark.postgres

client = TestClient(app)
WORKER_HEADERS = {"X-Actor-Role": "worker", "X-Actor-Id": "worker-1"}
OTHER_WORKER_HEADERS = {"X-Actor-Role": "worker", "X-Actor-Id": "worker-2"}
OPERATOR_HEADERS = {
    "X-Actor-Role": "operator",
    "X-Actor-Id": "operator-1",
    "X-Account-Id": "venue-1",
}
OTHER_VENUE_HEADERS = {
    "X-Actor-Role": "operator",
    "X-Actor-Id": "operator-2",
    "X-Account-Id": "venue-2",
}


def _seed_booking(repo_session, state: BookingState = BookingState.CHECKED_OUT) -> None:
    now = datetime(2030, 1, 1, 12, 0, tzinfo=UTC)
    repo_session.add(
        OrganisationModel(
            organisation_id="org-1",
            name="Bath Hospitality",
            country="GB",
            currency="GBP",
            created_at=now,
        )
    )
    repo_session.flush()
    repo_session.add(
        VenueModel(
            venue_id="venue-1",
            organisation_id="org-1",
            market_id="bath-gb",
            name="The Bath House",
            country="GB",
            currency="GBP",
            created_at=now,
            avatar_url="https://cdn.example.com/venue.webp",
        )
    )
    repo_session.add(
        WorkerProfileModel(
            worker_id="worker-1",
            display_name="Alex Morgan",
            role="Bartender",
            city="Bath",
            market_id="bath-gb",
            experience_years=2,
            reliability_score=1.0,
            badges=[],
            languages=["English"],
            updated_at=now,
            avatar_url="https://cdn.example.com/worker.webp",
        )
    )
    repo_session.flush()
    start = now - timedelta(hours=5)
    end = now - timedelta(hours=1)
    repo_session.add(
        ShiftModel(
            shift_id="shift-1",
            operator_id="operator-1",
            venue_id="venue-1",
            role="Bartender",
            location="12 North Parade, Bath",
            start_time=start,
            end_time=end,
            pay_rate=Decimal("15.50"),
            status="filled",
            created_at=now - timedelta(days=1),
            workers_needed=1,
            workers_filled=1,
            currency="GBP",
        )
    )
    repo_session.flush()
    repo_session.add(
        BookingModel(
            booking_id="booking-1",
            shift_id="shift-1",
            worker_id="worker-1",
            operator_id="operator-1",
            start_time=start,
            end_time=end,
            state=state,
            created_at=now - timedelta(days=1),
            checked_out_at=end if state != BookingState.CONFIRMED else None,
        )
    )
    repo_session.commit()


def test_pending_prompts_are_personalised_for_each_side(repo_session):
    _seed_booking(repo_session)

    worker = client.get("/ratings/pending", headers=WORKER_HEADERS)
    operator = client.get("/ratings/pending", headers=OPERATOR_HEADERS)

    assert worker.status_code == 200
    assert worker.json()[0]["target_name"] == "The Bath House"
    assert worker.json()[0]["shift_role"] == "Bartender"
    assert operator.status_code == 200
    assert operator.json()[0]["target_name"] == "Alex Morgan"


def test_rating_requires_booking_participation_and_venue_access(repo_session):
    _seed_booking(repo_session)

    worker = client.post(
        "/bookings/booking-1/rate",
        json={"stars": 5},
        headers=OTHER_WORKER_HEADERS,
    )
    operator = client.post(
        "/bookings/booking-1/rate",
        json={"stars": 5},
        headers=OTHER_VENUE_HEADERS,
    )

    assert worker.status_code == 403
    assert operator.status_code == 403


def test_rating_requires_completed_shift(repo_session):
    _seed_booking(repo_session, BookingState.CONFIRMED)

    response = client.post(
        "/bookings/booking-1/rate",
        json={"stars": 5},
        headers=WORKER_HEADERS,
    )

    assert response.status_code == 409
    assert client.get("/ratings/pending", headers=WORKER_HEADERS).json() == []


def test_rating_records_rater_and_clears_only_that_sides_prompt(repo_session):
    _seed_booking(repo_session)

    response = client.post(
        "/bookings/booking-1/rate",
        json={"stars": 5, "comment": "Clear briefing and a great team."},
        headers=WORKER_HEADERS,
    )

    assert response.status_code == 201
    repo_session.expire_all()
    rating = repo_session.query(RatingModel).one()
    assert rating.rated_by_role == "worker"
    assert rating.rater_id == "worker-1"
    assert client.get("/ratings/pending", headers=WORKER_HEADERS).json() == []
    assert len(client.get("/ratings/pending", headers=OPERATOR_HEADERS).json()) == 1


def test_worker_ratings_are_exposed_as_venue_reputation(repo_session):
    _seed_booking(repo_session)
    rated = client.post(
        "/bookings/booking-1/rate",
        json={"stars": 5},
        headers=WORKER_HEADERS,
    )

    summary = client.get("/venues/venue-1/rating-summary", headers=WORKER_HEADERS)

    assert rated.status_code == 201
    assert summary.status_code == 200
    assert summary.json() == {
        "venue_id": "venue-1",
        "avg_stars": 5.0,
        "total_ratings": 1,
    }


def test_each_side_can_rate_once(repo_session):
    _seed_booking(repo_session)
    first = client.post(
        "/bookings/booking-1/rate",
        json={"stars": 4},
        headers=OPERATOR_HEADERS,
    )
    duplicate = client.post(
        "/bookings/booking-1/rate",
        json={"stars": 3},
        headers=OPERATOR_HEADERS,
    )

    assert first.status_code == 201
    assert duplicate.status_code == 409


def test_rating_comment_is_bounded(repo_session):
    _seed_booking(repo_session)
    response = client.post(
        "/bookings/booking-1/rate",
        json={"stars": 5, "comment": "x" * 1001},
        headers=WORKER_HEADERS,
    )
    assert response.status_code == 422

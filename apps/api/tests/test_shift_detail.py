from datetime import UTC, datetime, timedelta
from decimal import Decimal
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from apps.api.src import main
from apps.api.src.deps import (
    get_application_repo,
    get_booking_repo,
    get_organisation_repo,
    get_shift_repo,
)
from apps.api.src.models.application import Application
from apps.api.src.models.organisation import Venue
from apps.api.src.models.shift import Shift
from apps.api.src.repositories.in_memory_application_repository import InMemoryApplicationRepository
from apps.api.src.repositories.in_memory_booking_repository import InMemoryBookingRepository
from apps.api.src.repositories.in_memory_organisation_repository import InMemoryOrganisationRepository
from apps.api.src.repositories.in_memory_shift_repository import InMemoryShiftRepository
from packages.domain.src.booking import Booking
from packages.domain.src.booking_state import BookingState

WORKER = {"X-Actor-Role": "worker", "X-Actor-Id": "worker-1"}
NOW = datetime(2030, 3, 12, 9, 0, tzinfo=UTC)
SHIFT_ID = "shift-goat"


@pytest.fixture
def client():
    bookings = InMemoryBookingRepository()
    shifts = InMemoryShiftRepository(bookings)
    bookings.attach_shift_repo(shifts)
    applications = InMemoryApplicationRepository()
    applications.attach_shift_repo(shifts)
    venues = InMemoryOrganisationRepository()
    venues.save_venue(
        Venue(
            venue_id="venue-1",
            organisation_id="org-1",
            name="The Goat",
            country="GB",
            currency="GBP",
            created_at=NOW,
        )
    )
    shifts.save(
        Shift(
            shift_id=SHIFT_ID,
            operator_id="operator-1",
            account_id="venue-1",
            role="Bartender",
            location="Main bar",
            start_time=NOW + timedelta(hours=9),
            end_time=NOW + timedelta(hours=14),
            pay_rate=Decimal("13.00"),
            notes=None,
            status="filled",
            created_at=NOW,
            workers_needed=1,
            workers_filled=1,
            currency="GBP",
        )
    )
    main.app.dependency_overrides[get_booking_repo] = lambda: bookings
    main.app.dependency_overrides[get_shift_repo] = lambda: shifts
    main.app.dependency_overrides[get_application_repo] = lambda: applications
    main.app.dependency_overrides[get_organisation_repo] = lambda: venues
    yield TestClient(main.app), bookings, applications
    main.app.dependency_overrides.clear()


def _booking(bookings, state=BookingState.CONFIRMED):
    booking_id = str(uuid4())
    bookings.save(
        Booking(
            booking_id=booking_id,
            shift_id=SHIFT_ID,
            worker_id="worker-1",
            operator_id="operator-1",
            start_time=NOW + timedelta(hours=9),
            end_time=NOW + timedelta(hours=14),
            state=state,
            created_at=NOW,
        )
    )
    return booking_id


def test_a_workers_bookings_carry_the_venue_and_pay(client):
    api, bookings, _ = client
    booking_id = _booking(bookings)

    listed = api.get("/bookings?worker_id=worker-1", headers=WORKER).json()
    assert len(listed) == 1
    shift = listed[0]["shift"]
    assert shift["venue_name"] == "The Goat"
    assert shift["role"] == "Bartender"
    assert shift["location"] == "Main bar"
    assert shift["pay_rate"] == "13.00"
    assert shift["currency"] == "GBP"

    single = api.get(f"/bookings/{booking_id}", headers=WORKER).json()
    assert single["shift"]["venue_name"] == "The Goat"


def test_applications_carry_the_same_detail(client):
    api, _, applications = client
    applications.save(
        Application(
            application_id=str(uuid4()),
            shift_id=SHIFT_ID,
            worker_id="worker-1",
            operator_id="operator-1",
            message=None,
            status="applied",
            created_at=NOW,
            start_time=NOW + timedelta(hours=9),
            end_time=NOW + timedelta(hours=14),
            booking_id=None,
        )
    )

    listed = api.get("/applications?worker_id=worker-1", headers=WORKER).json()
    assert len(listed) == 1
    assert listed[0]["shift"]["venue_name"] == "The Goat"
    assert listed[0]["shift"]["role"] == "Bartender"


def test_a_missing_venue_leaves_the_name_empty_without_failing(client):
    api, bookings, _ = client
    shifts = main.app.dependency_overrides[get_shift_repo]()
    orphan = "shift-orphan"
    shifts.save(
        Shift(
            shift_id=orphan,
            operator_id="operator-1",
            account_id=None,
            role="Runner",
            location="Terrace",
            start_time=NOW + timedelta(days=1),
            end_time=NOW + timedelta(days=1, hours=5),
            pay_rate=Decimal("12.00"),
            notes=None,
            status="filled",
            created_at=NOW,
            workers_needed=1,
            workers_filled=1,
        )
    )
    bookings.save(
        Booking(
            booking_id=str(uuid4()),
            shift_id=orphan,
            worker_id="worker-1",
            operator_id="operator-1",
            start_time=NOW + timedelta(days=1),
            end_time=NOW + timedelta(days=1, hours=5),
            state=BookingState.CONFIRMED,
            created_at=NOW,
        )
    )

    listed = api.get("/bookings?worker_id=worker-1", headers=WORKER).json()
    orphaned = next(item for item in listed if item["shift_id"] == orphan)
    assert orphaned["shift"]["venue_name"] is None
    assert orphaned["shift"]["role"] == "Runner"

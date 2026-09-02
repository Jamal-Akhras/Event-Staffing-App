from dataclasses import replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient

from apps.api.src import main
from apps.api.src.models.booking_charge import BookingCharge
from apps.api.src.models.worker_profile import WorkerProfile
from apps.api.src.models.worker_relationship import WorkerRelationship
from apps.api.src.repository_dependencies import get_booking_charge_repo, get_worker_profile_repo
from apps.api.src.repository_dependencies_workforce import (
    shared_relationship_transition_repository,
    shared_worker_relationship_repository,
)

VENUE = "venue-1"
NOW = datetime(2030, 6, 1, 12, 0, tzinfo=UTC)
OPERATOR = {"X-Actor-Role": "operator", "X-Actor-Id": "operator-1", "X-Account-Id": VENUE}
OTHER = {"X-Actor-Role": "operator", "X-Actor-Id": "operator-2", "X-Account-Id": "venue-2"}


@pytest.fixture(autouse=True)
def clear_state():
    for repo in (shared_worker_relationship_repository(), shared_relationship_transition_repository()):
        repo.clear()
    yield
    for repo in (shared_worker_relationship_repository(), shared_relationship_transition_repository()):
        repo.clear()


def _profile(worker_id: str, name: str, recontact: bool = True) -> WorkerProfile:
    return WorkerProfile(
        worker_id=worker_id,
        display_name=name,
        role="Bartender",
        city="Bath",
        experience_years=2,
        reliability_score=0.9,
        badges=[],
        bio=None,
        languages=["en"],
        email=None,
        phone=None,
        address=None,
        emergency_contact=None,
        pay_rate=None,
        notes=None,
        updated_at=NOW,
        allow_venue_recontact=recontact,
    )


def _charge(worker_id: str, hours: str, wages: str, fee: str, when: datetime) -> BookingCharge:
    return BookingCharge(
        charge_id=f"chg-{worker_id}-{when.day}",
        booking_id=f"bk-{worker_id}-{when.day}",
        shift_id="shift-1",
        account_id=VENUE,
        worker_id=worker_id,
        worker_name="Worker",
        role="Bartender",
        period=when.strftime("%Y-%m"),
        start_time=when,
        end_time=when + timedelta(hours=5),
        completed_at=when,
        hours=Decimal(hours),
        pay_rate=Decimal("14.00"),
        wages=Decimal(wages),
        fee_percent=Decimal("8.00"),
        fee=Decimal(fee),
        total=Decimal(wages) + Decimal(fee),
        currency="GBP",
        fee_waived=False,
        waiver_code=None,
        recorded_at=when,
        worker_relationship="one_off",
    )


def _relationship(worker_id: str, relationship_type: str, status: str = "active") -> WorkerRelationship:
    return shared_worker_relationship_repository().save(
        WorkerRelationship(
            relationship_id=f"rel-{worker_id}",
            venue_id=VENUE,
            worker_id=worker_id,
            relationship_type=relationship_type,
            status=status,
            created_at=NOW,
            updated_at=NOW,
            agreed_rate=Decimal("13.50") if relationship_type == "permanent" else None,
        )
    )


@pytest.fixture()
def client(in_memory_repos):
    workers = in_memory_repos[get_worker_profile_repo]
    workers.save(_profile("worker-1", "Ana Ruiz"))
    workers.save(_profile("worker-2", "Sam Okafor"))
    workers.save(_profile("worker-3", "Priya Shah", recontact=False))

    charges = in_memory_repos[get_booking_charge_repo]
    charges.record(_charge("worker-1", "5.00", "70.00", "5.60", NOW - timedelta(days=10)))
    charges.record(_charge("worker-1", "3.00", "42.00", "3.36", NOW - timedelta(days=2)))
    charges.record(_charge("worker-3", "4.00", "56.00", "4.48", NOW - timedelta(days=20)))
    return TestClient(main.app)


def _directory(client: TestClient, headers=OPERATOR) -> list[dict]:
    response = client.get("/venues/me/people", headers=headers)
    assert response.status_code == 200, response.text
    return response.json()


def test_the_directory_shows_team_pool_and_one_off_together(client):
    _relationship("worker-1", "one_off")
    _relationship("worker-2", "permanent")
    _relationship("worker-3", "pool")

    rows = {row["display_name"]: row for row in _directory(client)}
    assert {row["relationship_type"] for row in rows.values()} == {"one_off", "permanent", "pool"}
    assert rows["Sam Okafor"]["agreed_rate"] == "13.50"


def test_hours_and_cost_come_from_the_frozen_charges(client):
    _relationship("worker-1", "one_off")
    row = _directory(client)[0]
    assert (row["shifts_with_you"], row["hours_with_you"]) == (2, "8.00")
    assert (row["wages_to_date"], row["fees_to_date"]) == ("112.00", "8.96")
    assert row["last_worked"].startswith("2030-05-30")


def test_someone_who_turned_off_recontact_is_still_listed_and_marked(client):
    _relationship("worker-3", "one_off")
    row = _directory(client)[0]
    assert row["display_name"] == "Priya Shah"
    assert row["allows_recontact"] is False


def test_a_person_with_no_history_still_appears(client):
    _relationship("worker-2", "permanent")
    row = _directory(client)[0]
    assert (row["shifts_with_you"], row["wages_to_date"]) == (0, "0.00")
    assert row["last_worked"] is None


def test_ending_a_relationship_keeps_them_in_the_directory(client):
    _relationship("worker-1", "permanent")
    response = client.post("/venues/me/people/worker-1/end", json={"reason": "Left"}, headers=OPERATOR)
    assert response.status_code == 200, response.text

    row = _directory(client)[0]
    assert row["status"] == "ended"
    assert row["end_date"] is not None


def test_a_venue_never_sees_another_venues_people(client):
    _relationship("worker-1", "permanent")
    assert _directory(client, OTHER) == []


def test_the_directory_reads_each_repository_once(client):
    _relationship("worker-1", "one_off")
    _relationship("worker-2", "permanent")

    charges = main.app.dependency_overrides[get_booking_charge_repo]()
    calls: list[str] = []
    original = charges.list_for_account
    charges.list_for_account = lambda *args, **kwargs: (calls.append("charges"), original(*args, **kwargs))[1]
    try:
        assert len(_directory(client)) == 2
    finally:
        charges.list_for_account = original
    assert calls == ["charges"]

from datetime import UTC, date, datetime, timedelta
from dataclasses import replace

import pytest
from fastapi.testclient import TestClient

from apps.api.src import main
from apps.api.src.models.account import Account
from apps.api.src.models.organisation import Venue
from apps.api.src.models.worker_profile import WorkerProfile
from apps.api.src.models.worker_relationship import WorkerRelationship
from apps.api.src.repository_dependencies import (
    get_account_repo,
    get_booking_repo,
    get_notification_repo,
    get_organisation_repo,
    get_rota_publication_repo,
    get_shift_repo,
    get_worker_profile_repo,
)
from apps.api.src.repository_dependencies import get_booking_transition_repo
from apps.api.src.repository_dependencies import shared_shift_offer_repository
from apps.api.src.repository_dependencies_workforce import (
    shared_relationship_transition_repository,
    shared_worker_relationship_repository,
)
from packages.domain.src.booking_state import BookingState

VENUE_ID = "venue-1"
NOW = datetime(2030, 6, 3, 9, 0, tzinfo=UTC)
WEEK_START = date(2030, 6, 10)
OPERATOR = {"X-Actor-Role": "operator", "X-Actor-Id": "operator-1", "X-Account-Id": VENUE_ID}
STAFF = {"X-Actor-Role": "worker", "X-Actor-Id": "staff-1"}
POOLER = {"X-Actor-Role": "worker", "X-Actor-Id": "pool-1"}


@pytest.fixture(autouse=True)
def clear_state():
    for repo in (shared_worker_relationship_repository(), shared_relationship_transition_repository(), shared_shift_offer_repository()):
        repo.clear()
    yield
    for repo in (shared_worker_relationship_repository(), shared_relationship_transition_repository(), shared_shift_offer_repository()):
        repo.clear()


def _relationship(worker_id: str, relationship_type: str, status: str = "active") -> None:
    shared_worker_relationship_repository().save(
        WorkerRelationship(
            relationship_id=f"rel-{worker_id}",
            venue_id=VENUE_ID,
            worker_id=worker_id,
            relationship_type=relationship_type,
            status=status,
            created_at=NOW,
            updated_at=NOW,
        )
    )


@pytest.fixture()
def client(in_memory_repos):
    in_memory_repos[get_account_repo].save(
        Account(
            account_id=VENUE_ID, name="The Grapes", country="GB", currency="GBP",
            created_at=NOW, market_id="bath-gb",
        )
    )
    in_memory_repos[get_organisation_repo].save_venue(
        Venue(
            venue_id=VENUE_ID, organisation_id="org-1", name="The Grapes", country="GB",
            currency="GBP", created_at=NOW, market_id="bath-gb",
        )
    )
    for worker_id in ("staff-1", "pool-1"):
        in_memory_repos[get_worker_profile_repo].save(
            WorkerProfile(
                worker_id=worker_id, display_name=worker_id, role="Bartender", city="Bath",
                experience_years=1, reliability_score=1.0, badges=[], bio=None, languages=["en"],
                email=None, phone=None, address=None, emergency_contact=None, pay_rate=None,
                notes=None, updated_at=NOW, market_id="bath-gb",
            )
        )
    _relationship("staff-1", "permanent")
    _relationship("pool-1", "pool")
    return TestClient(main.app)


def _draft(client, worker_id: str, day_offset: int = 0, hour: int = 18, hours: int = 5) -> dict:
    start = datetime(2030, 6, 10 + day_offset, hour, 0, tzinfo=UTC)
    response = client.post(
        "/shifts",
        json={
            "role": "Bartender",
            "location": "Main bar",
            "start_time": start.isoformat(),
            "end_time": (start + timedelta(hours=hours)).isoformat(),
            "pay_rate": 14.5,
            "workers_needed": 1,
            "assigned_worker_id": worker_id,
            "rota_state": "draft",
            "now": NOW.isoformat(),
        },
        headers={**OPERATOR, "X-Actor-Verified": "true"},
    )
    assert response.status_code == 200, response.text
    return response.json()


def _publish(client, week_start: date = WEEK_START, headers: dict | None = None):
    return client.post(
        "/venues/me/rota/publish",
        json={"week_start": week_start.isoformat(), "now": NOW.isoformat()},
        headers=headers or OPERATOR,
    )


def test_publishing_books_employed_staff_and_offers_to_pool_members(client, in_memory_repos):
    staffed = _draft(client, "staff-1", day_offset=0)
    pooled = _draft(client, "pool-1", day_offset=1)

    response = _publish(client)
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["booked_worker_ids"] == ["staff-1"]
    assert body["offered_worker_ids"] == ["pool-1"]
    assert body["publication"]["revision"] == 1
    assert len(body["publication"]["assignments"]) == 2

    bookings = in_memory_repos[get_booking_repo].list_by_worker("staff-1")
    assert len(bookings) == 1
    assert bookings[0].state == BookingState.CONFIRMED
    assert bookings[0].attendance_mode == "employed"
    transitions = in_memory_repos[get_booking_transition_repo].list_for_booking(bookings[0].booking_id)
    assert [t.reason_code for t in transitions] == ["rota_published"]

    staffed_shift = in_memory_repos[get_shift_repo].get(staffed["shift_id"])
    assert (staffed_shift.rota_state, staffed_shift.status) == ("published", "filled")
    assert staffed_shift.billable is False

    pooled_shift = in_memory_repos[get_shift_repo].get(pooled["shift_id"])
    assert (pooled_shift.rota_state, pooled_shift.origin) == ("published", "assigned")
    assert pooled_shift.offer_pool_at is not None
    assert in_memory_repos[get_booking_repo].list_by_worker("pool-1") == []
    offers = shared_shift_offer_repository().list_for_worker("pool-1")
    assert [(offer.status, offer.source, offer.shift_id) for offer in offers] == [
        ("pending", "rota", pooled["shift_id"])
    ]
    assert offers[0].expires_at == pooled_shift.offer_pool_at

    notified = in_memory_repos[get_notification_repo].list_for_worker("staff-1", limit=10)
    staff_notice = next(item for item in notified if item.type == "rota.published")
    assert (staff_notice.action_kind, staff_notice.action_entity_id) == (
        "booking", bookings[0].booking_id,
    )
    pool_notice = next(
        item
        for item in in_memory_repos[get_notification_repo].list_for_worker("pool-1", limit=10)
        if item.type == "rota.published"
    )
    assert (pool_notice.action_kind, pool_notice.action_entity_id) == (
        "shift", pooled["shift_id"],
    )


def test_a_lapsed_assignee_blocks_publish_and_mutates_nothing(client, in_memory_repos):
    good = _draft(client, "staff-1", day_offset=0)
    _draft(client, "pool-1", day_offset=1)
    _relationship("pool-1", "pool", status="ended")

    response = _publish(client)
    assert response.status_code == 400
    assert "active relationship" in response.text

    assert in_memory_repos[get_booking_repo].list_by_worker("staff-1") == []
    assert in_memory_repos[get_shift_repo].get(good["shift_id"]).rota_state == "draft"
    assert in_memory_repos[get_rota_publication_repo].latest_for_week(VENUE_ID, WEEK_START) is None


def test_an_overlapping_draft_blocks_publish(client, in_memory_repos):
    _draft(client, "staff-1", day_offset=0, hour=18)
    _draft(client, "staff-1", day_offset=0, hour=20)

    response = _publish(client)
    assert response.status_code == 400
    assert "overlaps" in response.text
    assert in_memory_repos[get_booking_repo].list_by_worker("staff-1") == []


def test_publishing_an_unchanged_week_returns_the_same_revision(client):
    _draft(client, "staff-1")
    first = _publish(client).json()
    second = _publish(client)
    assert second.status_code == 200
    assert second.json()["publication"]["revision"] == first["publication"]["revision"]
    assert second.json()["publication"]["publication_id"] == first["publication"]["publication_id"]


def test_the_same_idempotency_key_replays_the_cached_response(client):
    from apps.api.src.config import use_in_memory_repositories

    if not use_in_memory_repositories():
        from apps.api.src.db.database import SessionLocal
        from apps.api.src.db.models import UserModel

        with SessionLocal() as session, session.begin():
            session.add(
                UserModel(
                    user_id="operator-1",
                    email="rota-idem@example.com",
                    hashed_password="x",
                    role="operator",
                    is_active=True,
                    created_at=NOW,
                    updated_at=NOW,
                    email_verified=True,
                )
            )
    _draft(client, "staff-1")
    headers = {**OPERATOR, "Idempotency-Key": "pub-1"}
    first = _publish(client, headers=headers).json()
    replay = _publish(client, headers=headers)
    assert replay.json()["publication"]["publication_id"] == first["publication"]["publication_id"]


def test_reassignment_is_one_revision_and_never_leaks_an_offer(client, in_memory_repos):
    drafted = _draft(client, "staff-1")
    _publish(client)
    booking = in_memory_repos[get_booking_repo].list_by_worker("staff-1")[0]

    response = client.post(
        f"/venues/me/rota/shifts/{drafted['shift_id']}/reassign",
        json={"worker_id": "pool-1", "now": NOW.isoformat()},
        headers=OPERATOR,
    )
    assert response.status_code == 200, response.text

    cancelled = in_memory_repos[get_booking_repo].get(booking.booking_id)
    assert cancelled.state == BookingState.CANCELLED_BY_OPERATOR
    offers = shared_shift_offer_repository().list_for_worker("pool-1")
    assert [(offer.status, offer.source) for offer in offers] == [("pending", "rota")]

    publications = client.get(
        "/venues/me/rota/publications", params={"week_start": WEEK_START.isoformat()}, headers=OPERATOR
    ).json()
    assert publications[-1]["revision"] == 2
    kinds = [change["kind"] for change in publications[-1]["changes"]]
    assert kinds == ["reassigned"]
    assert publications[-1]["changes"][0]["previous_worker_id"] == "staff-1"
    assert publications[-1]["changes"][0]["worker_id"] == "pool-1"

    from apps.api.tests.test_gap_escalation import _service

    assert _service(in_memory_repos).sweep(NOW + timedelta(days=60)) == []
    shift = in_memory_repos[get_shift_repo].get(drafted["shift_id"])
    assert shift.origin == "assigned"
    assert shift.rota_state == "published"


def test_a_failed_reassignment_rolls_back_nothing(client, in_memory_repos):
    _relationship("staff-2", "permanent")
    first = _draft(client, "staff-1", day_offset=0, hour=18)
    _draft(client, "staff-2", day_offset=0, hour=20)
    _publish(client)

    response = client.post(
        f"/venues/me/rota/shifts/{first['shift_id']}/reassign",
        json={"worker_id": "staff-2", "now": NOW.isoformat()},
        headers=OPERATOR,
    )
    assert response.status_code == 400
    assert "overlap" in response.text.lower()

    booking = in_memory_repos[get_booking_repo].list_by_worker("staff-1")[0]
    assert booking.state == BookingState.CONFIRMED
    assert in_memory_repos[get_shift_repo].get(first["shift_id"]).rota_state == "published"


def test_update_times_syncs_the_booking_and_mints_a_time_change(client, in_memory_repos):
    drafted = _draft(client, "staff-1")
    _publish(client)

    new_start = datetime(2030, 6, 10, 19, 0, tzinfo=UTC)
    response = client.post(
        f"/venues/me/rota/shifts/{drafted['shift_id']}/times",
        json={
            "start_time": new_start.isoformat(),
            "end_time": (new_start + timedelta(hours=5)).isoformat(),
            "now": NOW.isoformat(),
        },
        headers=OPERATOR,
    )
    assert response.status_code == 200, response.text

    booking = in_memory_repos[get_booking_repo].list_by_worker("staff-1")[0]
    assert booking.start_time == new_start

    publications = client.get(
        "/venues/me/rota/publications", params={"week_start": WEEK_START.isoformat()}, headers=OPERATOR
    ).json()
    assert [c["kind"] for c in publications[-1]["changes"]] == ["time_changed"]


def test_remove_cancels_shift_and_booking_with_one_notification(client, in_memory_repos):
    drafted = _draft(client, "staff-1")
    _publish(client)
    before = len(in_memory_repos[get_notification_repo].list_for_worker("staff-1", limit=50))

    response = client.post(
        f"/venues/me/rota/shifts/{drafted['shift_id']}/remove",
        json={"reason": "Quiet night, shift stood down", "now": NOW.isoformat()},
        headers=OPERATOR,
    )
    assert response.status_code == 200, response.text
    assert response.json()["status"] == "cancelled"

    booking = in_memory_repos[get_booking_repo].list_by_worker("staff-1")[0]
    assert booking.state == BookingState.CANCELLED_BY_OPERATOR

    after = in_memory_repos[get_notification_repo].list_for_worker("staff-1", limit=50)
    assert len(after) == before + 1

    publications = client.get(
        "/venues/me/rota/publications", params={"week_start": WEEK_START.isoformat()}, headers=OPERATOR
    ).json()
    assert [c["kind"] for c in publications[-1]["changes"]] == ["removed"]


def test_remove_rejects_started_attendance_without_mutating_the_shift(client, in_memory_repos):
    drafted = _draft(client, "staff-1")
    _publish(client)
    booking_repo = in_memory_repos[get_booking_repo]
    booking = booking_repo.list_by_worker("staff-1")[0]
    booking_repo.save(
        replace(
            booking,
            state=BookingState.CHECKED_OUT,
            checked_in_at=booking.start_time,
            checked_out_at=booking.end_time,
        )
    )

    response = client.post(
        f"/venues/me/rota/shifts/{drafted['shift_id']}/remove",
        json={"reason": "This must use the timesheet", "now": NOW.isoformat()},
        headers=OPERATOR,
    )

    assert response.status_code == 400
    assert in_memory_repos[get_shift_repo].get(drafted["shift_id"]).status == "filled"
    assert booking_repo.get(booking.booking_id).state == BookingState.CHECKED_OUT
    publications = in_memory_repos[get_rota_publication_repo].list_for_week(VENUE_ID, WEEK_START)
    assert len(publications) == 1


def test_past_confirmed_shift_cannot_be_reassigned(client, in_memory_repos):
    drafted = _draft(client, "staff-1")
    _publish(client)
    booking = in_memory_repos[get_booking_repo].list_by_worker("staff-1")[0]

    response = client.post(
        f"/venues/me/rota/shifts/{drafted['shift_id']}/reassign",
        json={"worker_id": "pool-1", "now": drafted["start_time"]},
        headers=OPERATOR,
    )

    assert response.status_code == 400
    shift = in_memory_repos[get_shift_repo].get(drafted["shift_id"])
    assert (shift.assigned_worker_id, shift.rota_state) == ("staff-1", "published")
    assert in_memory_repos[get_booking_repo].get(booking.booking_id).state == BookingState.CONFIRMED
    publications = in_memory_repos[get_rota_publication_repo].list_for_week(VENUE_ID, WEEK_START)
    assert len(publications) == 1


def test_another_venue_cannot_publish_or_mutate(client):
    drafted = _draft(client, "staff-1")
    other = {"X-Actor-Role": "operator", "X-Actor-Id": "operator-2", "X-Account-Id": "venue-2"}
    assert client.post(
        f"/venues/me/rota/shifts/{drafted['shift_id']}/remove",
        json={"reason": "not mine"},
        headers=other,
    ).status_code == 404

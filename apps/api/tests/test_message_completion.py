from dataclasses import replace
from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient

from apps.api.src import main
from apps.api.src.deps import (
    get_booking_repo,
    get_event_repo,
    get_organisation_repo,
    get_shift_repo,
    get_worker_relationship_repo,
)
from apps.api.src.models.event import EventQuery
from apps.api.src.models.organisation import Organisation, OrganisationMembership, OrganisationRole, Venue
from apps.api.src.models.shift import Shift
from apps.api.src.models.worker_relationship import WorkerRelationship
from packages.domain.src.booking import Booking
from packages.domain.src.booking_state import BookingState

MANAGER_ONE = {
    "X-Actor-Role": "operator", "X-Actor-Id": "manager-1", "X-Account-Id": "venue-1",
    "X-Organisation-Id": "org-1",
}
MANAGER_TWO = {
    "X-Actor-Role": "operator", "X-Actor-Id": "manager-2", "X-Account-Id": "venue-1",
    "X-Organisation-Id": "org-1",
}
OTHER_MANAGER = {
    "X-Actor-Role": "operator", "X-Actor-Id": "manager-3", "X-Account-Id": "venue-2",
    "X-Organisation-Id": "org-2",
}
WORKER_ONE = {"X-Actor-Role": "worker", "X-Actor-Id": "worker-1"}
WORKER_TWO = {"X-Actor-Role": "worker", "X-Actor-Id": "worker-2"}
STRANGER = {"X-Actor-Role": "worker", "X-Actor-Id": "worker-3"}


def _seed(in_memory_repos) -> tuple[TestClient, datetime]:
    now = datetime.now(UTC).replace(microsecond=0)
    organisations = in_memory_repos[get_organisation_repo]
    organisations.save_organisation(Organisation("org-1", "Group One", "GB", "GBP", now))
    organisations.save_organisation(Organisation("org-2", "Group Two", "GB", "GBP", now))
    organisations.save_venue(Venue("venue-1", "org-1", "Harbour Bar", "GB", "GBP", now))
    organisations.save_venue(Venue("venue-2", "org-2", "Other Bar", "GB", "GBP", now))
    for user_id in ("manager-1", "manager-2"):
        organisations.save_membership(
            OrganisationMembership("org-1", user_id, OrganisationRole.MANAGER, now, ("venue-1",))
        )
    shifts = in_memory_repos[get_shift_repo]
    bookings = in_memory_repos[get_booking_repo]
    shifts.save(_shift("shift-1", "venue-1", "manager-1", now, "Bartender"))
    shifts.save(_shift("shift-2", "venue-2", "manager-3", now, "Server"))
    bookings.save(_booking("booking-1", "shift-1", "worker-1", now))
    bookings.save(_booking("booking-2", "shift-1", "worker-2", now))
    bookings.save(_booking("booking-3", "shift-2", "worker-3", now))
    relationships = in_memory_repos[get_worker_relationship_repo]
    relationships.save(_relationship("rel-employed", "venue-1", "worker-1", "permanent", now))
    relationships.save(_relationship("rel-one-off", "venue-1", "worker-2", "one_off", now))
    return TestClient(main.app), now


def test_group_thread_participation_intervals_and_stranger_refusal(in_memory_repos):
    client, now = _seed(in_memory_repos)

    opened = client.get("/shifts/shift-1/group-thread", headers=MANAGER_ONE)
    assert opened.status_code == 200
    assert opened.json()["kind"] == "shift_group"
    assert client.get("/shifts/shift-1/group-thread", headers=STRANGER).status_code == 403

    first = client.post(
        "/shifts/shift-1/group-thread/messages", json={"content": "Briefing at five."},
        headers=MANAGER_ONE,
    )
    assert first.status_code == 200
    reply = client.post(
        "/shifts/shift-1/group-thread/messages", json={"content": "On my way."},
        headers=WORKER_ONE,
    )
    assert reply.status_code == 200
    assert [row["content"] for row in client.get(
        "/shifts/shift-1/group-thread", headers=WORKER_TWO
    ).json()["messages"]] == ["Briefing at five.", "On my way."]

    bookings = in_memory_repos[get_booking_repo]
    bookings.save(replace(bookings.get("booking-2"), state=BookingState.CANCELLED_BY_WORKER, cancelled_at=now))
    later = client.post(
        "/shifts/shift-1/group-thread/messages", json={"content": "Updated door code."},
        headers=MANAGER_TWO,
    )
    assert later.status_code == 200
    former = client.get("/shifts/shift-1/group-thread", headers=WORKER_TWO)
    assert former.status_code == 200
    assert [row["content"] for row in former.json()["messages"]] == [
        "Briefing at five.", "On my way."
    ]
    refused = client.post(
        "/shifts/shift-1/group-thread/messages", json={"content": "Can I still attend?"},
        headers=WORKER_TWO,
    )
    assert refused.status_code == 403


def test_per_participant_reads_and_manager_sender_identity(in_memory_repos):
    client, _ = _seed(in_memory_repos)
    client.get("/shifts/shift-1/group-thread", headers=MANAGER_ONE)
    worker_message = client.post(
        "/shifts/shift-1/group-thread/messages", json={"content": "I am running late."},
        headers=WORKER_ONE,
    ).json()
    manager_one_message = client.post(
        "/shifts/shift-1/group-thread/messages", json={"content": "Thanks for letting us know."},
        headers=MANAGER_ONE,
    ).json()
    manager_two_message = client.post(
        "/shifts/shift-1/group-thread/messages", json={"content": "Use the side door."},
        headers=MANAGER_TWO,
    ).json()

    assert manager_one_message["sender_id"] == "manager-1"
    assert manager_two_message["sender_id"] == "manager-2"
    read = client.post("/shifts/shift-1/group-thread/read", headers=MANAGER_ONE)
    assert read.json()["marked"] == 2
    manager_one_view = client.get("/shifts/shift-1/group-thread", headers=MANAGER_ONE).json()
    manager_two_view = client.get("/shifts/shift-1/group-thread", headers=MANAGER_TWO).json()
    one = next(row for row in manager_one_view["messages"] if row["message_id"] == worker_message["message_id"])
    two = next(row for row in manager_two_view["messages"] if row["message_id"] == worker_message["message_id"])
    assert one["read_at"] is not None
    assert two["read_at"] is None


def test_employment_channels_require_active_employed_relationship(in_memory_repos):
    client, _ = _seed(in_memory_repos)

    worker_threads = client.get("/me/employment-threads", headers=WORKER_ONE)
    venue_threads = client.get("/venues/me/employment-threads", headers=MANAGER_ONE)
    assert [row["relationship_id"] for row in worker_threads.json()] == ["rel-employed"]
    assert [row["relationship_id"] for row in venue_threads.json()] == ["rel-employed"]
    assert client.get("/me/employment-threads", headers=WORKER_TWO).json() == []
    assert client.get("/employment-threads/rel-one-off", headers=WORKER_TWO).status_code == 404

    sent = client.post(
        "/employment-threads/rel-employed/messages", json={"content": "Your rota is published."},
        headers=MANAGER_ONE,
    )
    assert sent.status_code == 200
    worker_view = client.get("/employment-threads/rel-employed", headers=WORKER_ONE)
    assert worker_view.status_code == 200
    assert worker_view.json()["messages"][0]["content"] == "Your rota is published."


def test_message_export_is_formula_safe_scoped_and_audited(in_memory_repos):
    client, now = _seed(in_memory_repos)
    client.get("/shifts/shift-1/group-thread", headers=MANAGER_ONE)
    group = client.post(
        "/shifts/shift-1/group-thread/messages", json={"content": "=SUM(1,1)"},
        headers=WORKER_ONE,
    )
    employment = client.post(
        "/employment-threads/rel-employed/messages", json={"content": "Permanent record"},
        headers=MANAGER_ONE,
    )
    client.get("/shifts/shift-2/group-thread", headers=OTHER_MANAGER)
    client.post(
        "/shifts/shift-2/group-thread/messages", json={"content": "Other venue secret"},
        headers=OTHER_MANAGER,
    )

    export = client.get(
        f"/venues/me/messages/export?month={now:%Y-%m}", headers=MANAGER_ONE
    )
    assert export.status_code == 200
    assert "shift_group" in export.text
    assert "employment" in export.text
    assert "'=SUM(1,1)" in export.text
    assert "Other venue secret" not in export.text
    assert "=SUM(1,1)" in client.get(
        "/shifts/shift-1/group-thread", headers=WORKER_ONE
    ).text

    events = in_memory_repos[get_event_repo].query(EventQuery(name="message.created"))
    ids = {event.subject_id for event in events}
    assert {group.json()["message_id"], employment.json()["message_id"]}.issubset(ids)
    assert all(event.context["thread_id"] for event in events)


def _shift(shift_id: str, venue_id: str, operator_id: str, now: datetime, role: str) -> Shift:
    return Shift(
        shift_id=shift_id,
        operator_id=operator_id,
        account_id=venue_id,
        role=role,
        location="Bath",
        start_time=now + timedelta(days=2),
        end_time=now + timedelta(days=2, hours=5),
        pay_rate=14,
        notes=None,
        status="filled",
        created_at=now,
        workers_needed=2,
        workers_filled=2,
    )


def _booking(booking_id: str, shift_id: str, worker_id: str, now: datetime) -> Booking:
    return Booking(
        booking_id=booking_id,
        shift_id=shift_id,
        worker_id=worker_id,
        operator_id="manager-1",
        start_time=now + timedelta(days=2),
        end_time=now + timedelta(days=2, hours=5),
        state=BookingState.CONFIRMED,
        created_at=now,
    )


def _relationship(
    relationship_id: str, venue_id: str, worker_id: str, relationship_type: str, now: datetime
) -> WorkerRelationship:
    return WorkerRelationship(
        relationship_id=relationship_id,
        venue_id=venue_id,
        worker_id=worker_id,
        relationship_type=relationship_type,
        status="active",
        default_role="Bartender",
        created_at=now,
        updated_at=now,
    )

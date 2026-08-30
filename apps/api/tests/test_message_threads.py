from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient

from apps.api.src import main
from apps.api.src.deps import get_application_repo, get_booking_charge_repo, get_booking_repo, get_booking_transition_repo, get_message_repo, get_shift_repo
from apps.api.src.models.application import Application
from apps.api.src.models.shift import Shift
from apps.api.src.repositories.in_memory_application_repository import InMemoryApplicationRepository
from apps.api.src.repositories.in_memory_booking_repository import InMemoryBookingRepository
from apps.api.src.repositories.in_memory_message_repository import InMemoryMessageRepository
from apps.api.src.repositories.in_memory_shift_repository import InMemoryShiftRepository
from apps.api.src.repository_dependencies import shared_booking_charge_repository, shared_booking_transition_repository
from packages.domain.src.booking import Booking
from packages.domain.src.booking_state import BookingState

VENUE_OWNER = {"X-Actor-Role": "operator", "X-Actor-Id": "operator-1", "X-Account-Id": "venue-1"}
VENUE_COLLEAGUE = {"X-Actor-Role": "operator", "X-Actor-Id": "operator-3", "X-Account-Id": "venue-1"}
OTHER_VENUE = {"X-Actor-Role": "operator", "X-Actor-Id": "operator-2", "X-Account-Id": "venue-2"}
WORKER = {"X-Actor-Role": "worker", "X-Actor-Id": "worker-1"}


def _client() -> TestClient:
    now = datetime(2030, 1, 1, 9, 0, 0, tzinfo=UTC)
    booking_repo = InMemoryBookingRepository()
    shift_repo = InMemoryShiftRepository(booking_repo)
    application_repo = InMemoryApplicationRepository()
    application_repo.attach_shift_repo(shift_repo)
    booking_repo.attach_shift_repo(shift_repo)
    message_repo = InMemoryMessageRepository()
    shift_repo.save(
        Shift(
            shift_id="shift-1",
            operator_id="operator-1",
            account_id="venue-1",
            role="bartender",
            location="Main bar",
            start_time=now + timedelta(days=2),
            end_time=now + timedelta(days=2, hours=5),
            pay_rate=14,
            notes=None,
            status="filled",
            created_at=now,
            workers_needed=1,
            workers_filled=1,
        )
    )
    application_repo.save(
        Application(
            application_id="app-1",
            shift_id="shift-1",
            worker_id="worker-1",
            operator_id="operator-1",
            start_time=now + timedelta(days=2),
            end_time=now + timedelta(days=2, hours=5),
            message=None,
            booking_id="bk-1",
            status="approved",
            created_at=now,
            decided_at=now,
        )
    )
    booking_repo.save(
        Booking(
            booking_id="bk-1",
            shift_id="shift-1",
            worker_id="worker-1",
            operator_id="operator-1",
            start_time=now + timedelta(days=2),
            end_time=now + timedelta(days=2, hours=5),
            state=BookingState.CONFIRMED,
            created_at=now,
        )
    )
    main.app.dependency_overrides.clear()
    main.app.dependency_overrides[get_shift_repo] = lambda: shift_repo
    main.app.dependency_overrides[get_application_repo] = lambda: application_repo
    main.app.dependency_overrides[get_message_repo] = lambda: message_repo
    main.app.dependency_overrides[get_booking_repo] = lambda: booking_repo
    main.app.dependency_overrides[get_booking_transition_repo] = shared_booking_transition_repository
    main.app.dependency_overrides[get_booking_charge_repo] = shared_booking_charge_repository
    return TestClient(main.app)


def test_application_and_booking_are_one_conversation():
    client = _client()

    sent_by_venue = client.post(
        "/shifts/shift-1/messages",
        json={"application_id": "app-1", "content": "Please arrive 15 minutes early."},
        headers=VENUE_OWNER,
    )
    assert sent_by_venue.status_code == 200
    assert sent_by_venue.json()["booking_id"] == "bk-1"

    sent_by_worker = client.post(
        "/shifts/shift-1/messages",
        json={"booking_id": "bk-1", "content": "Will do."},
        headers=WORKER,
    )
    assert sent_by_worker.status_code == 200
    assert sent_by_worker.json()["application_id"] == "app-1"

    seen_by_worker = client.get("/shifts/shift-1/messages?booking_id=bk-1", headers=WORKER)
    seen_by_venue = client.get("/shifts/shift-1/messages?application_id=app-1", headers=VENUE_OWNER)
    assert [m["content"] for m in seen_by_worker.json()] == ["Please arrive 15 minutes early.", "Will do."]
    assert seen_by_venue.json() == seen_by_worker.json()


def test_venue_colleagues_share_the_thread_but_other_venues_do_not():
    client = _client()
    client.post(
        "/shifts/shift-1/messages",
        json={"booking_id": "bk-1", "content": "Running five minutes late."},
        headers=WORKER,
    )

    colleague = client.get("/shifts/shift-1/messages?application_id=app-1", headers=VENUE_COLLEAGUE)
    assert colleague.status_code == 200
    assert colleague.json()[0]["content"] == "Running five minutes late."

    stranger = client.get("/shifts/shift-1/messages?application_id=app-1", headers=OTHER_VENUE)
    assert stranger.status_code == 403


def test_marking_a_thread_read_only_touches_the_other_side():
    client = _client()
    for content in ("First", "Second"):
        client.post("/shifts/shift-1/messages", json={"booking_id": "bk-1", "content": content}, headers=WORKER)
    client.post("/shifts/shift-1/messages", json={"application_id": "app-1", "content": "Noted"}, headers=VENUE_OWNER)

    marked = client.post("/shifts/shift-1/messages/read", json={"application_id": "app-1"}, headers=VENUE_OWNER)
    assert marked.status_code == 200
    assert marked.json()["marked"] == 2

    listed = client.get("/shifts/shift-1/messages?application_id=app-1", headers=VENUE_OWNER).json()
    read_state = {m["content"]: m["read_at"] is not None for m in listed}
    assert read_state == {"First": True, "Second": True, "Noted": False}

    again = client.post("/shifts/shift-1/messages/read", json={"application_id": "app-1"}, headers=VENUE_OWNER)
    assert again.json()["marked"] == 0


def test_blank_messages_are_rejected_and_content_is_trimmed():
    client = _client()

    blank = client.post("/shifts/shift-1/messages", json={"booking_id": "bk-1", "content": "   "}, headers=WORKER)
    assert blank.status_code == 422

    padded = client.post("/shifts/shift-1/messages", json={"booking_id": "bk-1", "content": "  hi  "}, headers=WORKER)
    assert padded.status_code == 200
    assert padded.json()["content"] == "hi"


def test_rapid_sends_get_distinct_ids():
    client = _client()
    ids = {
        client.post("/shifts/shift-1/messages", json={"booking_id": "bk-1", "content": f"m{i}"}, headers=WORKER).json()["message_id"]
        for i in range(5)
    }
    assert len(ids) == 5


def test_sender_cannot_mark_own_message_read():
    client = _client()
    sent = client.post("/shifts/shift-1/messages", json={"booking_id": "bk-1", "content": "Hello"}, headers=WORKER)

    own = client.post(f"/messages/{sent.json()['message_id']}/read", headers=WORKER)
    assert own.status_code == 403

    venue = client.post(f"/messages/{sent.json()['message_id']}/read", headers=VENUE_OWNER)
    assert venue.status_code == 200

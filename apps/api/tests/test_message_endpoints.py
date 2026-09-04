from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient

from apps.api.src import main
from apps.api.src.auth import ActorContext, ActorRole, get_actor_context
from apps.api.src.deps import get_application_repo, get_booking_charge_repo, get_booking_repo, get_booking_transition_repo, get_message_repo, get_message_thread_repo, get_organisation_repo, get_shift_repo
from apps.api.src.models.application import Application
from apps.api.src.models.organisation import Organisation, Venue
from apps.api.src.models.shift import Shift
from apps.api.src.repositories.in_memory_application_repository import InMemoryApplicationRepository
from apps.api.src.repositories.in_memory_booking_repository import InMemoryBookingRepository
from apps.api.src.repositories.in_memory_message_repository import InMemoryMessageRepository
from apps.api.src.repositories.in_memory_message_thread_repository import InMemoryMessageThreadRepository
from apps.api.src.repositories.in_memory_organisation_repository import InMemoryOrganisationRepository
from apps.api.src.repositories.in_memory_shift_repository import InMemoryShiftRepository
from apps.api.src.repository_dependencies import shared_booking_charge_repository, shared_booking_transition_repository

OPERATOR_HEADERS = {"X-Actor-Role": "operator", "X-Actor-Id": "operator-1", "X-Account-Id": "venue-1"}
OTHER_OPERATOR_HEADERS = {"X-Actor-Role": "operator", "X-Actor-Id": "operator-2", "X-Account-Id": "venue-2"}
WORKER_HEADERS = {"X-Actor-Role": "worker", "X-Actor-Id": "worker-1"}
OTHER_WORKER_HEADERS = {"X-Actor-Role": "worker", "X-Actor-Id": "worker-2"}


def _client() -> TestClient:
    now = datetime(2030, 1, 1, 9, 0, 0, tzinfo=UTC)
    booking_repo = InMemoryBookingRepository()
    shift_repo = InMemoryShiftRepository(booking_repo)
    application_repo = InMemoryApplicationRepository()
    application_repo.attach_shift_repo(shift_repo)
    booking_repo.attach_shift_repo(shift_repo)
    message_repo = InMemoryMessageRepository()
    thread_repo = InMemoryMessageThreadRepository()
    organisation_repo = InMemoryOrganisationRepository()
    organisation_repo.save_organisation(Organisation("org-1", "Group", "GB", "GBP", now))
    organisation_repo.save_venue(Venue("venue-1", "org-1", "Venue", "GB", "GBP", now))
    shift_repo.save(
        Shift(
            shift_id="shift-1",
            operator_id="operator-1",
            account_id="venue-1",
            role="server",
            location="Downtown",
            start_time=now + timedelta(hours=2),
            end_time=now + timedelta(hours=6),
            pay_rate=25,
            notes=None,
            status="open",
            created_at=now,
            workers_needed=1,
        )
    )
    application_repo.save(
        Application(
            application_id="app-1",
            shift_id="shift-1",
            worker_id="worker-1",
            operator_id="operator-1",
            start_time=now + timedelta(hours=2),
            end_time=now + timedelta(hours=6),
            message="available",
            booking_id=None,
            status="pending",
            created_at=now,
        )
    )
    main.app.dependency_overrides.clear()
    main.app.dependency_overrides[get_shift_repo] = lambda: shift_repo
    main.app.dependency_overrides[get_application_repo] = lambda: application_repo
    main.app.dependency_overrides[get_message_repo] = lambda: message_repo
    main.app.dependency_overrides[get_message_thread_repo] = lambda: thread_repo
    main.app.dependency_overrides[get_organisation_repo] = lambda: organisation_repo
    main.app.dependency_overrides[get_booking_repo] = lambda: booking_repo
    main.app.dependency_overrides[get_booking_transition_repo] = shared_booking_transition_repository
    main.app.dependency_overrides[get_booking_charge_repo] = shared_booking_charge_repository
    return TestClient(main.app)


def test_worker_can_message_own_application_thread():
    client = _client()

    create = client.post(
        "/shifts/shift-1/messages",
        json={"application_id": "app-1", "content": "I can make this shift."},
        headers=WORKER_HEADERS,
    )

    assert create.status_code == 200
    assert create.json()["sender_id"] == "worker-1"

    listed = client.get(
        "/shifts/shift-1/messages?application_id=app-1",
        headers=WORKER_HEADERS,
    )
    assert listed.status_code == 200
    assert listed.json()[0]["content"] == "I can make this shift."


def test_message_threads_are_limited_to_participants():
    client = _client()

    worker = client.get(
        "/shifts/shift-1/messages?application_id=app-1",
        headers=OTHER_WORKER_HEADERS,
    )
    assert worker.status_code == 403

    operator = client.post(
        "/shifts/shift-1/messages",
        json={"application_id": "app-1", "content": "Can you arrive early?"},
        headers=OTHER_OPERATOR_HEADERS,
    )
    assert operator.status_code == 403

    owner = client.post(
        "/shifts/shift-1/messages",
        json={"application_id": "app-1", "content": "Can you arrive early?"},
        headers=OPERATOR_HEADERS,
    )
    assert owner.status_code == 200


def test_linked_worker_account_uses_profile_id_for_message_access():
    client = _client()
    main.app.dependency_overrides[get_actor_context] = lambda: ActorContext(
        user_id="login-user-1",
        role=ActorRole.WORKER,
        worker_profile_id="worker-1",
    )

    try:
        response = client.post(
            "/shifts/shift-1/messages",
            json={"application_id": "app-1", "content": "I can make this shift."},
        )
    finally:
        main.app.dependency_overrides.pop(get_actor_context, None)

    assert response.status_code == 200
    assert response.json()["sender_id"] == "worker-1"

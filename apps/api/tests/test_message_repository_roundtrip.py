from datetime import UTC, datetime

import pytest

from apps.api.src.db.models import OrganisationModel, VenueModel
from apps.api.src.db.workforce_models import WorkerRelationshipModel
from apps.api.src.models.message import Message, MessageReadReceipt, MessageThread, MessageThreadParticipant
from apps.api.src.repositories.sqlalchemy_message_repository import SqlAlchemyMessageRepository
from apps.api.src.repositories.sqlalchemy_message_thread_repository import SqlAlchemyMessageThreadRepository


def test_message_thread_repository_full_field_round_trip(repo_session):
    now = datetime(2030, 2, 1, 10, 30, tzinfo=UTC)
    repo_session.add(OrganisationModel(
        organisation_id="org-message", name="Group", country="GB", currency="GBP", created_at=now
    ))
    repo_session.add(VenueModel(
        venue_id="venue-message", organisation_id="org-message", name="Harbour Bar",
        country="GB", currency="GBP", created_at=now,
    ))
    repo_session.add(WorkerRelationshipModel(
        relationship_id="rel-message", venue_id="venue-message", worker_id="worker-message",
        relationship_type="permanent", status="active", default_role="Bartender",
        created_at=now, updated_at=now,
    ))
    repo_session.flush()
    threads = SqlAlchemyMessageThreadRepository(repo_session)
    messages = SqlAlchemyMessageRepository(repo_session)
    thread = MessageThread(
        thread_id="thread-message",
        kind="employment",
        venue_id="venue-message",
        shift_id=None,
        application_id=None,
        booking_id=None,
        relationship_id="rel-message",
        worker_id="worker-message",
        role_snapshot="Bartender",
        venue_name_snapshot="Harbour Bar",
        created_at=now,
    )
    participant = MessageThreadParticipant(
        participant_id="participant-message",
        thread_id=thread.thread_id,
        party_kind="worker",
        party_id="worker-message",
        joined_at=now,
        left_at=None,
    )
    message = Message(
        message_id="message-round-trip",
        thread_id=thread.thread_id,
        sender_id="manager-message",
        sender_role="operator",
        content="Your rota is ready.",
        created_at=now,
    )
    receipt = MessageReadReceipt(
        receipt_id="receipt-message",
        message_id=message.message_id,
        party_kind="worker",
        party_id="worker-message",
        read_at=now,
    )

    assert threads.save(thread) == thread
    assert threads.save_participant(participant) == participant
    assert messages.save(message) == message
    assert threads.save_receipt(receipt) == receipt
    repo_session.expire_all()

    assert threads.get(thread.thread_id) == thread
    assert threads.get_employment("rel-message") == thread
    assert threads.list_for_venue("venue-message") == [thread]
    assert threads.list_employment_for_worker("worker-message") == [thread]
    assert threads.list_participants(thread.thread_id) == [participant]
    assert messages.get(message.message_id) == message
    assert messages.list_by_thread(thread.thread_id) == [message]
    assert threads.get_receipt(message.message_id, "worker", "worker-message") == receipt


def test_message_repository_refuses_body_mutation(repo_session):
    now = datetime(2030, 2, 1, 10, 30, tzinfo=UTC)
    repo_session.add(OrganisationModel(
        organisation_id="org-immutable", name="Group", country="GB", currency="GBP", created_at=now
    ))
    repo_session.add(VenueModel(
        venue_id="venue-immutable", organisation_id="org-immutable", name="Harbour Bar",
        country="GB", currency="GBP", created_at=now,
    ))
    repo_session.add(WorkerRelationshipModel(
        relationship_id="rel-immutable", venue_id="venue-immutable", worker_id="worker-immutable",
        relationship_type="bank", status="active", created_at=now, updated_at=now,
    ))
    repo_session.flush()
    threads = SqlAlchemyMessageThreadRepository(repo_session)
    messages = SqlAlchemyMessageRepository(repo_session)
    threads.save(MessageThread(
        thread_id="thread-immutable", kind="employment", venue_id="venue-immutable",
        shift_id=None, application_id=None, booking_id=None, relationship_id="rel-immutable",
        worker_id="worker-immutable", role_snapshot="bank", venue_name_snapshot="Harbour Bar",
        created_at=now,
    ))
    original = Message(
        message_id="message-immutable", thread_id="thread-immutable", sender_id="worker-immutable",
        sender_role="worker", content="Original", created_at=now,
    )
    messages.save(original)

    with pytest.raises(ValueError, match="immutable"):
        messages.save(original.model_copy(update={"content": "Changed"}))

    assert messages.get(original.message_id) == original

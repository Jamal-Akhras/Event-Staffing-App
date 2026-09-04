from __future__ import annotations

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from apps.api.src.db.message_models import (
    MessageReadReceiptModel,
    MessageThreadModel,
    MessageThreadParticipantModel,
)
from apps.api.src.models.message import MessageReadReceipt, MessageThread, MessageThreadParticipant
from apps.api.src.repositories.in_memory_message_thread_repository import _validate_thread_update

THREAD_FIELDS = tuple(MessageThread.model_fields)


class SqlAlchemyMessageThreadRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def get(self, thread_id: str) -> MessageThread | None:
        row = self._session.get(MessageThreadModel, thread_id)
        return _thread(row) if row else None

    def save(self, thread: MessageThread) -> MessageThread:
        with self._session.begin_nested():
            row = self._session.get(MessageThreadModel, thread.thread_id)
            if row is None:
                self._session.add(MessageThreadModel(**thread.model_dump()))
            else:
                existing = _thread(row)
                _validate_thread_update(existing, thread)
                row.application_id = thread.application_id
                row.booking_id = thread.booking_id
            self._session.flush()
        return thread

    def get_direct(self, shift_id: str, worker_id: str) -> MessageThread | None:
        return self._one(kind="direct", shift_id=shift_id, worker_id=worker_id)

    def get_shift_group(self, shift_id: str) -> MessageThread | None:
        return self._one(kind="shift_group", shift_id=shift_id)

    def get_employment(self, relationship_id: str) -> MessageThread | None:
        return self._one(kind="employment", relationship_id=relationship_id)

    def list_for_venue(self, venue_id: str) -> list[MessageThread]:
        return self._list(MessageThreadModel.venue_id == venue_id)

    def list_employment_for_worker(self, worker_id: str) -> list[MessageThread]:
        return self._list(
            MessageThreadModel.kind == "employment",
            MessageThreadModel.worker_id == worker_id,
        )

    def save_participant(self, participant: MessageThreadParticipant) -> MessageThreadParticipant:
        with self._session.begin_nested():
            row = self._session.get(MessageThreadParticipantModel, participant.participant_id)
            if row is not None:
                if _participant(row) != participant:
                    raise ValueError("Participant intervals cannot be rewritten.")
                return participant
            self._session.add(MessageThreadParticipantModel(**_participant_values(participant)))
            self._session.flush()
        return participant

    def close_participant(self, participant_id: str, left_at: datetime) -> MessageThreadParticipant:
        with self._session.begin_nested():
            row = self._session.get(MessageThreadParticipantModel, participant_id)
            if row is None:
                raise ValueError("Participant interval does not exist.")
            if row.left_at is None:
                row.left_at = left_at
                self._session.flush()
            return _participant(row)

    def list_participants(self, thread_id: str) -> list[MessageThreadParticipant]:
        rows = self._session.execute(
            select(MessageThreadParticipantModel)
            .where(MessageThreadParticipantModel.thread_id == thread_id)
            .order_by(
                MessageThreadParticipantModel.joined_at,
                MessageThreadParticipantModel.participant_id,
            )
        ).scalars().all()
        return [_participant(row) for row in rows]

    def get_receipt(
        self, message_id: str, party_kind: str, party_id: str
    ) -> MessageReadReceipt | None:
        condition = (
            MessageReadReceiptModel.user_id == party_id
            if party_kind == "user"
            else MessageReadReceiptModel.worker_id == party_id
        )
        row = self._session.execute(
            select(MessageReadReceiptModel).where(
                MessageReadReceiptModel.message_id == message_id,
                MessageReadReceiptModel.party_kind == party_kind,
                condition,
            )
        ).scalar_one_or_none()
        return _receipt(row) if row else None

    def save_receipt(self, receipt: MessageReadReceipt) -> MessageReadReceipt:
        with self._session.begin_nested():
            existing = self.get_receipt(receipt.message_id, receipt.party_kind, receipt.party_id)
            if existing is not None:
                return existing
            self._session.add(MessageReadReceiptModel(**_receipt_values(receipt)))
            self._session.flush()
        return receipt

    def _one(self, **values) -> MessageThread | None:
        query = select(MessageThreadModel)
        for name, value in values.items():
            query = query.where(getattr(MessageThreadModel, name) == value)
        row = self._session.execute(query).scalar_one_or_none()
        return _thread(row) if row else None

    def _list(self, *conditions) -> list[MessageThread]:
        rows = self._session.execute(
            select(MessageThreadModel)
            .where(*conditions)
            .order_by(MessageThreadModel.created_at, MessageThreadModel.thread_id)
        ).scalars().all()
        return [_thread(row) for row in rows]


def _thread(row: MessageThreadModel) -> MessageThread:
    return MessageThread(**{name: getattr(row, name) for name in THREAD_FIELDS})


def _participant(row: MessageThreadParticipantModel) -> MessageThreadParticipant:
    return MessageThreadParticipant(
        participant_id=row.participant_id,
        thread_id=row.thread_id,
        party_kind=row.party_kind,
        party_id=row.user_id if row.party_kind == "user" else row.worker_id,
        joined_at=row.joined_at,
        left_at=row.left_at,
    )


def _participant_values(participant: MessageThreadParticipant) -> dict:
    return {
        "participant_id": participant.participant_id,
        "thread_id": participant.thread_id,
        "party_kind": participant.party_kind,
        "user_id": participant.party_id if participant.party_kind == "user" else None,
        "worker_id": participant.party_id if participant.party_kind == "worker" else None,
        "joined_at": participant.joined_at,
        "left_at": participant.left_at,
    }


def _receipt(row: MessageReadReceiptModel) -> MessageReadReceipt:
    return MessageReadReceipt(
        receipt_id=row.receipt_id,
        message_id=row.message_id,
        party_kind=row.party_kind,
        party_id=row.user_id if row.party_kind == "user" else row.worker_id,
        read_at=row.read_at,
    )


def _receipt_values(receipt: MessageReadReceipt) -> dict:
    return {
        "receipt_id": receipt.receipt_id,
        "message_id": receipt.message_id,
        "party_kind": receipt.party_kind,
        "user_id": receipt.party_id if receipt.party_kind == "user" else None,
        "worker_id": receipt.party_id if receipt.party_kind == "worker" else None,
        "read_at": receipt.read_at,
    }

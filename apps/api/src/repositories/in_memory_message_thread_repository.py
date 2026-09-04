from __future__ import annotations

from datetime import datetime

from apps.api.src.models.message import MessageReadReceipt, MessageThread, MessageThreadParticipant


class InMemoryMessageThreadRepository:
    def __init__(self) -> None:
        self._threads: dict[str, MessageThread] = {}
        self._participants: dict[str, MessageThreadParticipant] = {}
        self._receipts: dict[tuple[str, str, str], MessageReadReceipt] = {}

    def get(self, thread_id: str) -> MessageThread | None:
        return self._threads.get(thread_id)

    def save(self, thread: MessageThread) -> MessageThread:
        existing = self._threads.get(thread.thread_id)
        if existing is not None:
            _validate_thread_update(existing, thread)
        self._threads[thread.thread_id] = thread
        return thread

    def get_direct(self, shift_id: str, worker_id: str) -> MessageThread | None:
        return self._find(kind="direct", shift_id=shift_id, worker_id=worker_id)

    def get_shift_group(self, shift_id: str) -> MessageThread | None:
        return self._find(kind="shift_group", shift_id=shift_id)

    def get_employment(self, relationship_id: str) -> MessageThread | None:
        return self._find(kind="employment", relationship_id=relationship_id)

    def list_for_venue(self, venue_id: str) -> list[MessageThread]:
        return self._ordered(thread for thread in self._threads.values() if thread.venue_id == venue_id)

    def list_employment_for_worker(self, worker_id: str) -> list[MessageThread]:
        return self._ordered(
            thread
            for thread in self._threads.values()
            if thread.kind == "employment" and thread.worker_id == worker_id
        )

    def save_participant(self, participant: MessageThreadParticipant) -> MessageThreadParticipant:
        existing = self._participants.get(participant.participant_id)
        if existing is not None and existing != participant:
            raise ValueError("Participant intervals cannot be rewritten.")
        self._participants[participant.participant_id] = participant
        return participant

    def close_participant(self, participant_id: str, left_at: datetime) -> MessageThreadParticipant:
        participant = self._participants.get(participant_id)
        if participant is None:
            raise ValueError("Participant interval does not exist.")
        if participant.left_at is not None:
            return participant
        closed = participant.model_copy(update={"left_at": left_at})
        self._participants[participant_id] = closed
        return closed

    def list_participants(self, thread_id: str) -> list[MessageThreadParticipant]:
        return sorted(
            (row for row in self._participants.values() if row.thread_id == thread_id),
            key=lambda row: (row.joined_at, row.participant_id),
        )

    def get_receipt(
        self, message_id: str, party_kind: str, party_id: str
    ) -> MessageReadReceipt | None:
        return self._receipts.get((message_id, party_kind, party_id))

    def save_receipt(self, receipt: MessageReadReceipt) -> MessageReadReceipt:
        key = (receipt.message_id, receipt.party_kind, receipt.party_id)
        existing = self._receipts.get(key)
        if existing is not None:
            return existing
        self._receipts[key] = receipt
        return receipt

    def clear(self) -> None:
        self._threads.clear()
        self._participants.clear()
        self._receipts.clear()

    def _find(self, **values) -> MessageThread | None:
        for thread in self._threads.values():
            if all(getattr(thread, name) == value for name, value in values.items()):
                return thread
        return None

    @staticmethod
    def _ordered(threads) -> list[MessageThread]:
        return sorted(threads, key=lambda thread: (thread.created_at, thread.thread_id))


def _validate_thread_update(existing: MessageThread, updated: MessageThread) -> None:
    immutable = (
        "kind", "venue_id", "shift_id", "relationship_id", "worker_id",
        "role_snapshot", "venue_name_snapshot", "created_at",
    )
    if any(getattr(existing, name) != getattr(updated, name) for name in immutable):
        raise ValueError("Message thread identity and snapshots are immutable.")
    for name in ("application_id", "booking_id"):
        old = getattr(existing, name)
        new = getattr(updated, name)
        if old is not None and old != new:
            raise ValueError("Direct message context cannot be replaced.")

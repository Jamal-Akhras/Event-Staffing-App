from __future__ import annotations

from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from apps.api.src.db.message_models import MessageModel, MessageThreadModel
from apps.api.src.models.message import Message


class SqlAlchemyMessageRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def get(self, message_id: str) -> Message | None:
        model = self._session.get(MessageModel, message_id)
        return _to_domain(model) if model else None

    def save(self, message: Message) -> Message:
        with self._session.begin_nested():
            existing = self._session.get(MessageModel, message.message_id)
            if existing is not None:
                if _to_domain(existing) != message:
                    raise ValueError("Messages are immutable.")
                return message
            self._session.add(MessageModel(**message.model_dump()))
            self._session.flush()
        return message

    def list_by_shift(self, shift_id: str, limit: int = 100) -> list[Message]:
        return self._latest(MessageThreadModel.shift_id == shift_id, limit)

    def list_by_thread(self, thread_id: str, limit: int = 100) -> list[Message]:
        rows = self._session.execute(
            select(MessageModel)
            .where(MessageModel.thread_id == thread_id)
            .order_by(desc(MessageModel.created_at), desc(MessageModel.message_id))
            .limit(limit)
        ).scalars().all()
        return [_to_domain(row) for row in reversed(rows)]

    def list_by_application(self, application_id: str, limit: int = 100) -> list[Message]:
        return self._latest(MessageThreadModel.application_id == application_id, limit)

    def list_by_booking(self, booking_id: str, limit: int = 100) -> list[Message]:
        return self._latest(MessageThreadModel.booking_id == booking_id, limit)

    def list_for_threads_between(self, thread_ids: list[str], since, until) -> list[Message]:
        if not thread_ids:
            return []
        rows = self._session.execute(
            select(MessageModel)
            .where(
                MessageModel.thread_id.in_(thread_ids),
                MessageModel.created_at >= since,
                MessageModel.created_at < until,
            )
            .order_by(MessageModel.created_at, MessageModel.message_id)
        ).scalars().all()
        return [_to_domain(row) for row in rows]

    def _latest(self, condition, limit: int) -> list[Message]:
        rows = self._session.execute(
            select(MessageModel)
            .join(MessageThreadModel, MessageThreadModel.thread_id == MessageModel.thread_id)
            .where(condition)
            .order_by(desc(MessageModel.created_at), desc(MessageModel.message_id))
            .limit(limit)
        ).scalars().all()
        return [_to_domain(row) for row in reversed(rows)]


def _to_domain(model: MessageModel) -> Message:
    return Message(
        message_id=model.message_id,
        thread_id=model.thread_id,
        sender_id=model.sender_id,
        sender_role=model.sender_role,
        content=model.content,
        created_at=model.created_at,
    )

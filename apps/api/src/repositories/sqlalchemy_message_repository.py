from __future__ import annotations

from sqlalchemy import desc
from sqlalchemy.orm import Session

from apps.api.src.db.models import MessageModel
from apps.api.src.datetime_utils import utc_now
from apps.api.src.models.message import Message


class SqlAlchemyMessageRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def get(self, message_id: str) -> Message | None:
        model = self._session.get(MessageModel, message_id)
        if model is None:
            return None
        return _to_domain(model)

    def save(self, message: Message) -> Message:
        model = self._session.get(MessageModel, message.message_id)
        if model is None:
            model = MessageModel(message_id=message.message_id)
            self._session.add(model)
        _apply_domain(model, message)
        self._session.flush()
        return message

    def list_by_shift(self, shift_id: str, limit: int = 100) -> list[Message]:
        rows = (
            self._session.query(MessageModel)
            .filter(MessageModel.shift_id == shift_id)
            .order_by(desc(MessageModel.created_at))
            .limit(limit)
            .all()
        )
        return [_to_domain(row) for row in reversed(rows)]

    def list_by_application(self, application_id: str, limit: int = 100) -> list[Message]:
        rows = (
            self._session.query(MessageModel)
            .filter(MessageModel.application_id == application_id)
            .order_by(desc(MessageModel.created_at))
            .limit(limit)
            .all()
        )
        return [_to_domain(row) for row in reversed(rows)]

    def list_by_booking(self, booking_id: str, limit: int = 100) -> list[Message]:
        rows = (
            self._session.query(MessageModel)
            .filter(MessageModel.booking_id == booking_id)
            .order_by(desc(MessageModel.created_at))
            .limit(limit)
            .all()
        )
        return [_to_domain(row) for row in reversed(rows)]

    def mark_as_read(self, message_id: str) -> bool:
        model = self._session.get(MessageModel, message_id)
        if model is None:
            return False
        model.read_at = utc_now()
        self._session.flush()
        return True


def _to_domain(model: MessageModel) -> Message:
    return Message(
        message_id=model.message_id,
        shift_id=model.shift_id,
        application_id=model.application_id,
        booking_id=model.booking_id,
        sender_id=model.sender_id,
        sender_role=model.sender_role,
        content=model.content,
        read_at=model.read_at,
        created_at=model.created_at,
    )


def _apply_domain(model: MessageModel, message: Message) -> None:
    model.shift_id = message.shift_id
    model.application_id = message.application_id
    model.booking_id = message.booking_id
    model.sender_id = message.sender_id
    model.sender_role = message.sender_role
    model.content = message.content
    model.read_at = message.read_at
    model.created_at = message.created_at

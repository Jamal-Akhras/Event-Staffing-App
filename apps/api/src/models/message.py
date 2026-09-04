from __future__ import annotations

from datetime import datetime
from pydantic import BaseModel, ConfigDict


class Message(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    message_id: str
    thread_id: str
    sender_id: str
    sender_role: str
    content: str
    created_at: datetime


class MessageThread(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    thread_id: str
    kind: str
    venue_id: str
    shift_id: str | None
    application_id: str | None
    booking_id: str | None
    relationship_id: str | None
    worker_id: str | None
    role_snapshot: str | None
    venue_name_snapshot: str
    created_at: datetime


class MessageThreadParticipant(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    participant_id: str
    thread_id: str
    party_kind: str
    party_id: str
    joined_at: datetime
    left_at: datetime | None


class MessageReadReceipt(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    receipt_id: str
    message_id: str
    party_kind: str
    party_id: str
    read_at: datetime


class MessageView(BaseModel):
    message_id: str
    thread_id: str
    thread_kind: str
    shift_id: str | None
    application_id: str | None
    booking_id: str | None
    relationship_id: str | None
    sender_id: str
    sender_role: str
    content: str
    read_at: datetime | None
    created_at: datetime


class MessageThreadView(BaseModel):
    thread: MessageThread
    messages: list[MessageView]
    can_post: bool

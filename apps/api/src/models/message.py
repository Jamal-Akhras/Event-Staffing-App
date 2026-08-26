from __future__ import annotations

from datetime import datetime
from pydantic import BaseModel, ConfigDict


class Message(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    message_id: str
    shift_id: str
    application_id: str | None
    booking_id: str | None
    sender_id: str
    sender_role: str
    content: str
    read_at: datetime | None
    created_at: datetime

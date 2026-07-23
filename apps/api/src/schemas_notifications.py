from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class NotificationResponse(BaseModel):
    notification_id: str
    type: str
    title: str
    body: str
    shift_id: str | None = None
    read: bool
    created_at: datetime

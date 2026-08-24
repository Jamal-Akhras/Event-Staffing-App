from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class Notification:
    notification_id: str
    worker_id: str | None
    type: str
    title: str
    body: str
    created_at: datetime
    venue_id: str | None = None
    shift_id: str | None = None
    action_kind: str | None = None
    action_entity_id: str | None = None
    delivery_id: str | None = None
    read: bool = False

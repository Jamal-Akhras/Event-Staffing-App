from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class Notification:
    notification_id: str
    worker_id: str
    type: str  # "approved" | "rejected" | "invited"
    title: str
    body: str
    created_at: datetime
    shift_id: str | None = None
    read: bool = False

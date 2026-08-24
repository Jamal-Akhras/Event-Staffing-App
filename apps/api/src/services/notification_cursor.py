from __future__ import annotations

import base64
from datetime import datetime


def encode_notification_cursor(created_at: datetime, notification_id: str) -> str:
    value = f"{created_at.isoformat()}|{notification_id}".encode("utf-8")
    return base64.urlsafe_b64encode(value).decode("ascii").rstrip("=")


def decode_notification_cursor(cursor: str | None) -> tuple[datetime, str] | None:
    if not cursor:
        return None
    try:
        padding = "=" * (-len(cursor) % 4)
        value = base64.urlsafe_b64decode(cursor + padding).decode("utf-8")
        timestamp, notification_id = value.split("|", 1)
        return datetime.fromisoformat(timestamp), notification_id
    except (ValueError, UnicodeDecodeError) as exc:
        raise ValueError("Invalid notification cursor.") from exc

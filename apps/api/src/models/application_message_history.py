from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class ApplicationMessageHistory:
    history_id: str
    application_id: str
    message: str
    edited_at: datetime

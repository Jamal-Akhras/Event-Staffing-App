from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class Application:
    application_id: str
    shift_id: str
    worker_id: str
    operator_id: str
    start_time: datetime
    end_time: datetime
    message: str | None
    booking_id: str | None
    status: str
    created_at: datetime
    decided_at: datetime | None = None
    withdrawn_at: datetime | None = None
    withdrawal_reason: str | None = None

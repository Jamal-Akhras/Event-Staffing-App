from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class Shift:
    shift_id: str
    operator_id: str
    role: str
    location: str
    start_time: datetime
    end_time: datetime
    pay_rate: float
    notes: str | None
    status: str
    created_at: datetime
    workers_needed: int  # Number of workers needed for this shift
    workers_filled: int = 0  # Number of workers currently assigned (confirmed bookings)

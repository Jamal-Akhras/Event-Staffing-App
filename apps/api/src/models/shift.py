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

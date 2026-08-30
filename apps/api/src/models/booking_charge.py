from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal


@dataclass(frozen=True)
class BookingCharge:
    charge_id: str
    booking_id: str
    shift_id: str
    account_id: str
    worker_id: str
    worker_name: str
    role: str
    period: str
    start_time: datetime
    end_time: datetime
    completed_at: datetime
    hours: Decimal
    pay_rate: Decimal
    wages: Decimal
    fee_percent: Decimal
    fee: Decimal
    total: Decimal
    currency: str
    fee_waived: bool
    waiver_code: str | None
    recorded_at: datetime

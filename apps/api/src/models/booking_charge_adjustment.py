from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal


@dataclass(frozen=True)
class BookingChargeAdjustment:
    adjustment_id: str
    charge_id: str
    booking_id: str
    delta_hours: Decimal
    delta_wages: Decimal
    delta_fee: Decimal
    reason: str
    created_by_user_id: str
    created_at: datetime

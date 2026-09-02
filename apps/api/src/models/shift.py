from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

SHIFT_ORIGINS = ("assigned", "pool", "market")


@dataclass(frozen=True)
class Shift:
    shift_id: str
    operator_id: str
    role: str
    location: str
    start_time: datetime
    end_time: datetime
    pay_rate: Decimal
    notes: str | None
    status: str
    created_at: datetime
    workers_needed: int
    workers_filled: int = 0
    account_id: str | None = None
    currency: str = "GBP"
    latitude: float | None = None
    longitude: float | None = None
    updated_at: datetime | None = None
    closed_at: datetime | None = None
    cancelled_at: datetime | None = None
    cancellation_reason: str | None = None
    cancelled_by_user_id: str | None = None
    origin: str = "market"
    assigned_worker_id: str | None = None
    billable: bool = True
    offer_pool_at: datetime | None = None
    publish_market_at: datetime | None = None

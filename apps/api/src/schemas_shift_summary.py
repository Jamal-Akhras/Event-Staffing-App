from __future__ import annotations

from pydantic import BaseModel

from apps.api.src.validation_types import MoneyAmount, UtcTimestamp


class ShiftSummaryResponse(BaseModel):
    shift_id: str
    role: str
    location: str
    pay_rate: MoneyAmount
    currency: str
    start_time: UtcTimestamp
    end_time: UtcTimestamp
    venue_id: str | None = None
    venue_name: str | None = None
    venue_avatar_url: str | None = None

from __future__ import annotations

from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field

from apps.api.src.validation_types import MoneyAmount, UtcTimestamp


class BillingLineResponse(BaseModel):
    line_id: str
    line_kind: Literal["charge", "correction"]
    charge_id: str
    adjustment_id: str | None
    reason: str | None
    booking_id: str
    shift_id: str
    worker_id: str
    worker_name: str
    role: str
    start_time: UtcTimestamp
    end_time: UtcTimestamp
    completed_at: UtcTimestamp
    hours: Decimal
    wages: Decimal
    fee: Decimal
    total: Decimal
    waived: bool
    state: str


class WaiverResponse(BaseModel):
    code: str
    label: str
    fee_waived_until: UtcTimestamp
    shift_cap: int
    shifts_used: int
    active: bool


class BillingSummaryResponse(BaseModel):
    month: str
    fee_percent: Decimal
    plan: str
    waiver: WaiverResponse | None
    lines: list[BillingLineResponse]
    wages_total: MoneyAmount
    fee_total: MoneyAmount
    amount_due: MoneyAmount
    completed_shifts_all_time: int


class RedeemPartnerCodeRequest(BaseModel):
    code: str = Field(min_length=4, max_length=32)

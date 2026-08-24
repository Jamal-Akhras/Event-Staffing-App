from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, model_validator

from apps.api.src.validation_types import MoneyAmount, UtcTimestamp


class CancellationRequest(BaseModel):
    reason: str = Field(min_length=3, max_length=500)
    now: UtcTimestamp | None = None


class ShiftLifecycleRequest(BaseModel):
    now: UtcTimestamp | None = None


class PaymentRecordRequest(BaseModel):
    confirmation: Literal["PAYMENT_SENT"]
    method: Literal["bank_transfer", "cash", "payroll", "other"]
    reference: str | None = Field(default=None, max_length=200)
    now: UtcTimestamp | None = None


class ShiftUpdateRequest(BaseModel):
    role: str = Field(min_length=1, max_length=120)
    location: str = Field(min_length=1, max_length=240)
    start_time: UtcTimestamp
    end_time: UtcTimestamp
    pay_rate: MoneyAmount
    notes: str | None = Field(default=None, max_length=2000)
    workers_needed: int = Field(ge=1, le=100)
    now: UtcTimestamp | None = None

    @model_validator(mode="after")
    def validate_time_order(self) -> "ShiftUpdateRequest":
        if self.end_time <= self.start_time:
            raise ValueError("end_time must be after start_time")
        return self

from __future__ import annotations

from decimal import Decimal

from pydantic import BaseModel, Field, model_validator

from apps.api.src.validation_types import MoneyAmount, UtcTimestamp


class OnboardingStepResponse(BaseModel):
    key: str
    title: str
    detail: str
    done: bool


class OnboardingResponse(BaseModel):
    steps: list[OnboardingStepResponse]
    summary: str


class ShiftPostRequest(BaseModel):
    role: str = Field(min_length=1, max_length=120)
    location: str = Field(min_length=1, max_length=240)
    start_time: UtcTimestamp
    end_time: UtcTimestamp
    pay_rate: MoneyAmount | None = None
    note: str | None = Field(default=None, max_length=500)

    @model_validator(mode="after")
    def _order(self) -> "ShiftPostRequest":
        if self.end_time <= self.start_time:
            raise ValueError("end_time must be after start_time")
        return self


class ShiftPostResponse(BaseModel):
    description: str
    suggested_pay_low: Decimal | None
    suggested_pay_high: Decimal | None
    pay_basis: str


class OfferMessageRequest(BaseModel):
    worker_id: str = Field(min_length=1, max_length=100)
    role: str = Field(min_length=1, max_length=120)
    start_time: UtcTimestamp
    pay_rate: MoneyAmount


class OfferMessageResponse(BaseModel):
    message: str

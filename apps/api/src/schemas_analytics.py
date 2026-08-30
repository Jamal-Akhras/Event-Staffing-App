from __future__ import annotations

from pydantic import BaseModel

from apps.api.src.validation_types import MoneyAmount, UtcTimestamp


class AnalyticsGapResponse(BaseModel):
    shift_id: str
    role: str
    location: str
    start_time: UtcTimestamp
    unfilled: int
    applications: int
    lead_time_hours: float
    pay_rate: MoneyAmount
    reason: str


class AnalyticsRoleResponse(BaseModel):
    role: str
    seats: int


class AnalyticsResponse(BaseModel):
    period: str
    window_start: UtcTimestamp
    window_end: UtcTimestamp
    seats_posted: int
    seats_filled: int
    fill_rate: float
    applications: int
    applications_per_seat: float
    hours_staffed: MoneyAmount
    average_pay_rate: MoneyAmount
    currency: str
    fill_rate_trend: list[float]
    applications_trend: list[float]
    hours_trend: list[float]
    rate_trend: list[float]
    gaps: list[AnalyticsGapResponse]
    roles: list[AnalyticsRoleResponse]

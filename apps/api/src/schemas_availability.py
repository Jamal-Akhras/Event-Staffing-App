from __future__ import annotations

from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import BaseModel, ConfigDict, Field, model_validator

from apps.api.src.models.availability import (
    AvailabilityExceptionKind,
    TimeOffStatus,
    WorkerAvailabilityStatus,
)


class AvailabilityRuleInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    timezone: str
    weekday: int = Field(ge=0, le=6)
    start_minute: int = Field(ge=0, le=1439)
    duration_minutes: int = Field(ge=1, le=1440)
    effective_from: date
    effective_until: date | None = None

    @model_validator(mode="after")
    def validate_dates(self) -> "AvailabilityRuleInput":
        try:
            ZoneInfo(self.timezone)
        except ZoneInfoNotFoundError as exc:
            raise ValueError("timezone must be a valid IANA timezone") from exc
        if self.effective_until is not None and self.effective_until < self.effective_from:
            raise ValueError("effective_until must not precede effective_from")
        return self


class AvailabilityRulesReplaceRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    rules: list[AvailabilityRuleInput]


class AvailabilityRuleResponse(AvailabilityRuleInput):
    rule_id: str
    worker_id: str
    created_at: datetime
    updated_at: datetime


class AvailabilityExceptionCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    kind: AvailabilityExceptionKind
    start_time: datetime
    end_time: datetime
    note: str | None = Field(default=None, max_length=500)

    @model_validator(mode="after")
    def validate_interval(self) -> "AvailabilityExceptionCreateRequest":
        _validate_interval(self.start_time, self.end_time)
        return self


class AvailabilityExceptionResponse(AvailabilityExceptionCreateRequest):
    exception_id: str
    worker_id: str
    created_at: datetime
    updated_at: datetime


class TimeOffCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    venue_id: str
    start_time: datetime
    end_time: datetime
    reason: str = Field(min_length=1, max_length=1000)

    @model_validator(mode="after")
    def validate_interval(self) -> "TimeOffCreateRequest":
        _validate_interval(self.start_time, self.end_time)
        return self


class TimeOffResponse(TimeOffCreateRequest):
    request_id: str
    worker_id: str
    status: TimeOffStatus
    created_at: datetime
    updated_at: datetime
    decided_at: datetime | None = None
    decided_by_user_id: str | None = None


class WorkerCurrentStatusResponse(BaseModel):
    worker_id: str
    status: WorkerAvailabilityStatus
    availability_configured: bool


def _validate_interval(start_time: datetime, end_time: datetime) -> None:
    if start_time.tzinfo is None or end_time.tzinfo is None:
        raise ValueError("timestamps must include a timezone")
    if end_time <= start_time:
        raise ValueError("end_time must be after start_time")
    if end_time - start_time > timedelta(days=366):
        raise ValueError("availability intervals cannot exceed 366 days")

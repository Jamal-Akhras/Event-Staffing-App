from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field, model_validator


class BookingCreateRequest(BaseModel):
    shift_id: str
    worker_id: str
    operator_id: str
    start_time: datetime
    end_time: datetime
    now: datetime | None = None

    @model_validator(mode="after")
    def validate_time_order(self) -> "BookingCreateRequest":
        if self.end_time <= self.start_time:
            raise ValueError("end_time must be after start_time")
        return self


class BookingTransitionRequest(BaseModel):
    now: datetime | None = None


class BookingResponse(BaseModel):
    booking_id: str
    shift_id: str
    worker_id: str
    operator_id: str
    start_time: datetime
    end_time: datetime
    state: str
    allowed_transitions: list[str]
    created_at: datetime | None = None
    confirmed_at: datetime | None = None
    checked_in_at: datetime | None = None
    checked_out_at: datetime | None = None
    approved_at: datetime | None = None
    paid_at: datetime | None = None
    cancelled_at: datetime | None = None
    no_show_at: datetime | None = None


class ShiftCreateRequest(BaseModel):
    role: str
    location: str
    start_time: datetime
    end_time: datetime
    pay_rate: float = Field(ge=0)
    notes: str | None = None
    workers_needed: int = Field(default=1, ge=1)
    now: datetime | None = None

    @model_validator(mode="after")
    def validate_time_order(self) -> "ShiftCreateRequest":
        if self.end_time <= self.start_time:
            raise ValueError("end_time must be after start_time")
        return self


class ShiftResponse(BaseModel):
    shift_id: str
    operator_id: str
    role: str
    location: str
    start_time: datetime
    end_time: datetime
    pay_rate: float
    notes: str | None = None
    status: str
    created_at: datetime
    workers_needed: int
    workers_filled: int
    currency: str = "GBP"
    latitude: float | None = None
    longitude: float | None = None


class ApplicationCreateRequest(BaseModel):
    shift_id: str
    worker_id: str
    message: str | None = None
    now: datetime | None = None


class ApplicationDecisionRequest(BaseModel):
    now: datetime | None = None


class ApplicationMessageUpdateRequest(BaseModel):
    message: str
    now: datetime | None = None


class ApplicationResponse(BaseModel):
    application_id: str
    shift_id: str
    worker_id: str
    operator_id: str
    start_time: datetime
    end_time: datetime
    status: str
    message: str | None = None
    booking_id: str | None = None
    created_at: datetime
    decided_at: datetime | None = None


class ApplicationMessageHistoryResponse(BaseModel):
    history_id: str
    application_id: str
    message: str
    edited_at: datetime


class WorkerProfileUpdateRequest(BaseModel):
    display_name: str
    role: str
    city: str
    experience_years: int = Field(ge=0)
    bio: str | None = None
    languages: list[str]
    email: str | None = None
    phone: str | None = None
    address: str | None = None
    emergency_contact: str | None = None
    pay_rate: float | None = Field(default=None, ge=0)
    notes: str | None = None
    allow_venue_recontact: bool = False
    now: datetime | None = None


class WorkerProfilePublicResponse(BaseModel):
    worker_id: str
    display_name: str
    role: str
    city: str
    experience_years: int
    reliability_score: float
    badges: list[str]
    bio: str | None = None
    languages: list[str]
    updated_at: datetime
    avatar_url: str | None = None


class WorkerProfilePrivateResponse(WorkerProfilePublicResponse):
    email: str | None = None
    phone: str | None = None
    address: str | None = None
    emergency_contact: str | None = None
    pay_rate: float | None = None
    notes: str | None = None
    allow_venue_recontact: bool = False


class ErrorResponse(BaseModel):
    detail: str = Field(..., description="Human-readable error message.")


class TemplateCreateRequest(BaseModel):
    name: str
    role: str
    location: str
    duration_hours: float = Field(gt=0)
    pay_rate: float = Field(ge=0)
    workers_needed: int = Field(default=1, ge=1)
    notes: str | None = None


class TemplateUpdateRequest(BaseModel):
    name: str
    role: str
    location: str
    duration_hours: float = Field(gt=0)
    pay_rate: float = Field(ge=0)
    workers_needed: int = Field(ge=1)
    notes: str | None = None


class TemplateResponse(BaseModel):
    template_id: str
    operator_id: str
    name: str
    role: str
    location: str
    duration_hours: float
    pay_rate: float
    workers_needed: int
    notes: str | None = None
    created_at: datetime
    updated_at: datetime


class GenerateShiftsRequest(BaseModel):
    start_date: datetime
    end_date: datetime
    start_time: str  # "HH:MM" format (e.g., "18:00")
    days_of_week: list[int] | None = None  # [0-6] where 0=Monday, 6=Sunday. None means every day.


class RecurringScheduleCreateRequest(BaseModel):
    template_id: str
    frequency: str  # "daily", "weekly", "monthly"
    day_of_week: int | None = None  # 0-6 for weekly schedules (0=Monday, 6=Sunday)
    time_of_day: str  # "HH:MM" format (e.g., "18:00")
    start_date: datetime
    end_date: datetime | None = None


class RecurringScheduleResponse(BaseModel):
    schedule_id: str
    template_id: str
    operator_id: str
    frequency: str
    day_of_week: int | None
    time_of_day: str
    start_date: datetime
    end_date: datetime | None
    is_active: bool
    created_at: datetime
    last_generated_at: datetime | None


class MessageSendRequest(BaseModel):
    content: str = Field(min_length=1)
    application_id: str | None = None
    booking_id: str | None = None


class MessageResponse(BaseModel):
    message_id: str
    shift_id: str
    application_id: str | None
    booking_id: str | None
    sender_id: str
    sender_role: str
    content: str
    read_at: datetime | None
    created_at: datetime


class EarningsEntryResponse(BaseModel):
    booking_id: str
    shift_id: str
    role: str
    location: str
    start_time: datetime
    end_time: datetime
    hours: float
    pay_rate: float
    total: float
    status: str
    currency: str = "GBP"


class EarningsSummaryResponse(BaseModel):
    period: str
    total_paid: float
    total_pending: float
    currency: str = "GBP"
    entries: list[EarningsEntryResponse]


class WorkerFeedStateUpdateRequest(BaseModel):
    action: str = Field(pattern="^passed$")
    now: datetime | None = None


class WorkerFeedStateResponse(BaseModel):
    worker_id: str
    shift_id: str
    action: str
    created_at: datetime
    updated_at: datetime

from __future__ import annotations

from pydantic import BaseModel, Field, field_validator, model_validator

from apps.api.src.validation_types import MoneyAmount, UtcTimestamp


class BookingTransitionRequest(BaseModel):
    now: UtcTimestamp | None = None


class BookingResponse(BaseModel):
    booking_id: str
    shift_id: str
    worker_id: str
    operator_id: str
    start_time: UtcTimestamp
    end_time: UtcTimestamp
    state: str
    allowed_transitions: list[str]
    created_at: UtcTimestamp | None = None
    confirmed_at: UtcTimestamp | None = None
    checked_in_at: UtcTimestamp | None = None
    checked_out_at: UtcTimestamp | None = None
    approved_at: UtcTimestamp | None = None
    paid_at: UtcTimestamp | None = None
    cancelled_at: UtcTimestamp | None = None
    cancellation_reason: str | None = None
    cancelled_by_user_id: str | None = None
    no_show_at: UtcTimestamp | None = None
    payment_method: str | None = None
    payment_reference: str | None = None
    payment_recorded_by_user_id: str | None = None


class ShiftCreateRequest(BaseModel):
    role: str = Field(min_length=1, max_length=120)
    location: str = Field(min_length=1, max_length=240)
    start_time: UtcTimestamp
    end_time: UtcTimestamp
    pay_rate: MoneyAmount
    notes: str | None = Field(default=None, max_length=2000)
    workers_needed: int = Field(default=1, ge=1, le=100)
    now: UtcTimestamp | None = None

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
    start_time: UtcTimestamp
    end_time: UtcTimestamp
    pay_rate: MoneyAmount
    notes: str | None = None
    status: str
    created_at: UtcTimestamp
    updated_at: UtcTimestamp | None = None
    workers_needed: int
    workers_filled: int
    currency: str = "GBP"
    latitude: float | None = None
    longitude: float | None = None
    closed_at: UtcTimestamp | None = None
    cancelled_at: UtcTimestamp | None = None
    cancellation_reason: str | None = None
    cancelled_by_user_id: str | None = None


class ApplicationCreateRequest(BaseModel):
    shift_id: str = Field(min_length=1, max_length=100)
    worker_id: str = Field(min_length=1, max_length=100)
    message: str | None = Field(default=None, max_length=2000)
    now: UtcTimestamp | None = None


class ApplicationDecisionRequest(BaseModel):
    now: UtcTimestamp | None = None


class ApplicationMessageUpdateRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2000)
    now: UtcTimestamp | None = None


class ApplicationResponse(BaseModel):
    application_id: str
    shift_id: str
    worker_id: str
    operator_id: str
    start_time: UtcTimestamp
    end_time: UtcTimestamp
    status: str
    message: str | None = None
    booking_id: str | None = None
    created_at: UtcTimestamp
    decided_at: UtcTimestamp | None = None
    withdrawn_at: UtcTimestamp | None = None
    withdrawal_reason: str | None = None


class ApplicationMessageHistoryResponse(BaseModel):
    history_id: str
    application_id: str
    message: str
    edited_at: UtcTimestamp


class WorkerProfileUpdateRequest(BaseModel):
    display_name: str = Field(max_length=120)
    role: str = Field(max_length=120)
    city: str = Field(max_length=120)
    experience_years: int = Field(ge=0, le=100)
    bio: str | None = Field(default=None, max_length=2000)
    languages: list[str] = Field(max_length=20)
    email: str | None = Field(default=None, max_length=254)
    phone: str | None = Field(default=None, max_length=50)
    address: str | None = Field(default=None, max_length=500)
    emergency_contact: str | None = Field(default=None, max_length=500)
    pay_rate: MoneyAmount | None = None
    notes: str | None = Field(default=None, max_length=2000)
    allow_venue_recontact: bool = False
    market_id: str | None = None
    now: UtcTimestamp | None = None


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
    updated_at: UtcTimestamp
    avatar_url: str | None = None
    market_id: str | None = None


class WorkerProfilePrivateResponse(WorkerProfilePublicResponse):
    email: str | None = None
    phone: str | None = None
    address: str | None = None
    emergency_contact: str | None = None
    pay_rate: MoneyAmount | None = None
    notes: str | None = None
    allow_venue_recontact: bool = False


class ErrorResponse(BaseModel):
    detail: str = Field(..., description="Human-readable error message.")


class TemplateCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    role: str = Field(min_length=1, max_length=120)
    location: str = Field(min_length=1, max_length=240)
    duration_hours: float = Field(gt=0, le=24)
    pay_rate: MoneyAmount
    workers_needed: int = Field(default=1, ge=1, le=100)
    notes: str | None = Field(default=None, max_length=2000)


class TemplateUpdateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    role: str = Field(min_length=1, max_length=120)
    location: str = Field(min_length=1, max_length=240)
    duration_hours: float = Field(gt=0, le=24)
    pay_rate: MoneyAmount
    workers_needed: int = Field(ge=1, le=100)
    notes: str | None = Field(default=None, max_length=2000)


class TemplateResponse(BaseModel):
    template_id: str
    operator_id: str
    name: str
    role: str
    location: str
    duration_hours: float
    pay_rate: MoneyAmount
    workers_needed: int
    notes: str | None = None
    created_at: UtcTimestamp
    updated_at: UtcTimestamp


class GenerateShiftsRequest(BaseModel):
    start_date: UtcTimestamp
    end_date: UtcTimestamp
    start_time: str
    days_of_week: list[int] | None = None


class RecurringScheduleCreateRequest(BaseModel):
    template_id: str
    frequency: str
    day_of_week: int | None = None
    time_of_day: str
    start_date: UtcTimestamp
    end_date: UtcTimestamp | None = None


class RecurringScheduleResponse(BaseModel):
    schedule_id: str
    template_id: str
    operator_id: str
    frequency: str
    day_of_week: int | None
    time_of_day: str
    start_date: UtcTimestamp
    end_date: UtcTimestamp | None
    is_active: bool
    created_at: UtcTimestamp
    last_generated_at: UtcTimestamp | None


class MessageSendRequest(BaseModel):
    content: str = Field(min_length=1, max_length=4000)
    application_id: str | None = None
    booking_id: str | None = None

    @field_validator("content")
    @classmethod
    def _require_visible_content(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("Message content cannot be blank.")
        return stripped


class MessageThreadReadRequest(BaseModel):
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
    read_at: UtcTimestamp | None
    created_at: UtcTimestamp


class EarningsEntryResponse(BaseModel):
    booking_id: str
    shift_id: str
    role: str
    location: str
    start_time: UtcTimestamp
    end_time: UtcTimestamp
    hours: float
    pay_rate: MoneyAmount
    total: MoneyAmount
    status: str
    currency: str = "GBP"


class EarningsSummaryResponse(BaseModel):
    period: str
    total_paid: MoneyAmount
    total_pending: MoneyAmount
    currency: str = "GBP"
    entries: list[EarningsEntryResponse]


class WorkerFeedStateUpdateRequest(BaseModel):
    action: str = Field(pattern="^passed$")
    now: UtcTimestamp | None = None


class WorkerFeedStateResponse(BaseModel):
    worker_id: str
    shift_id: str
    action: str
    created_at: UtcTimestamp
    updated_at: UtcTimestamp

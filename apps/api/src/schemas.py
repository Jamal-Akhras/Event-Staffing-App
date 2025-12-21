from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class BookingCreateRequest(BaseModel):
    shift_id: str
    worker_id: str
    operator_id: str
    start_time: datetime
    end_time: datetime
    now: datetime | None = None


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
    operator_id: str
    role: str
    location: str
    start_time: datetime
    end_time: datetime
    pay_rate: float
    notes: str | None = None
    now: datetime | None = None


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


class ApplicationCreateRequest(BaseModel):
    shift_id: str
    worker_id: str
    message: str | None = None
    now: datetime | None = None


class ApplicationDecisionRequest(BaseModel):
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


class WorkerProfileUpdateRequest(BaseModel):
    display_name: str
    role: str
    city: str
    experience_years: int
    bio: str | None = None
    languages: list[str]
    email: str | None = None
    phone: str | None = None
    address: str | None = None
    emergency_contact: str | None = None
    pay_rate: float | None = None
    notes: str | None = None
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


class WorkerProfilePrivateResponse(WorkerProfilePublicResponse):
    email: str | None = None
    phone: str | None = None
    address: str | None = None
    emergency_contact: str | None = None
    pay_rate: float | None = None
    notes: str | None = None


class ErrorResponse(BaseModel):
    detail: str = Field(..., description="Human-readable error message.")

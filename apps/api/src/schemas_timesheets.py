from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field

from apps.api.src.validation_types import UtcTimestamp

ApprovalResultCode = Literal[
    "approved", "needs_worker_code", "not_approvable_state", "not_found", "already_approved"
]


class TimesheetDayResponse(BaseModel):
    day: date
    booking_id: str
    charge_id: str | None
    shift_id: str
    role: str
    state: str
    attendance_mode: str
    scheduled_start: UtcTimestamp
    scheduled_end: UtcTimestamp
    scheduled_hours: Decimal
    worked_hours: Decimal | None
    hours_source: Literal["clocked", "adjusted", "venue_recorded", "scheduled", "approved"]
    approved_hours: Decimal | None
    approved_wages: Decimal | None
    adjustments_total_hours: Decimal


class TimesheetWorkerResponse(BaseModel):
    worker_id: str
    display_name: str
    relationship_type: str
    contracted_hours_per_week: Decimal | None
    scheduled_hours: Decimal
    worked_hours: Decimal
    approved_hours: Decimal
    days: list[TimesheetDayResponse]


class TimesheetWeekResponse(BaseModel):
    venue_id: str
    week_start: date
    workers: list[TimesheetWorkerResponse]
    total_scheduled_hours: Decimal
    total_worked_hours: Decimal
    total_approved_hours: Decimal
    total_approved_wages: Decimal


class TimesheetApproveRequest(BaseModel):
    booking_ids: list[str] = Field(min_length=1, max_length=100)
    now: UtcTimestamp | None = None


class TimesheetApprovalRow(BaseModel):
    booking_id: str
    result: ApprovalResultCode


class TimesheetApproveResponse(BaseModel):
    results: list[TimesheetApprovalRow]


class HoursAdjustRequest(BaseModel):
    checked_in_at: UtcTimestamp
    checked_out_at: UtcTimestamp
    reason: str = Field(min_length=3, max_length=500)
    now: UtcTimestamp | None = None


class AttendanceRecordRequest(BaseModel):
    checked_in_at: UtcTimestamp
    checked_out_at: UtcTimestamp
    now: UtcTimestamp | None = None


class ChargeCorrectionRequest(BaseModel):
    delta_hours: Decimal = Field(gt=Decimal("-100"), lt=Decimal("100"))
    reason: str = Field(min_length=3, max_length=500)
    now: UtcTimestamp | None = None


class ChargeCorrectionResponse(BaseModel):
    adjustment_id: str
    charge_id: str
    booking_id: str
    delta_hours: Decimal
    delta_wages: Decimal
    delta_fee: Decimal
    reason: str
    created_at: UtcTimestamp

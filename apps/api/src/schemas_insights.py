from __future__ import annotations

from datetime import date

from pydantic import BaseModel

from apps.api.src.schemas import ShiftResponse
from apps.api.src.validation_types import UtcTimestamp


class DayCoverageResponse(BaseModel):
    day: date
    total_shifts: int
    open_seats: int


class PendingApplicationsResponse(BaseModel):
    count: int
    oldest_created_at: UtcTimestamp | None


class AttendanceResponse(BaseModel):
    completed: int
    no_shows: int
    total: int
    rate: int | None


class TonightWorkerResponse(BaseModel):
    booking_id: str
    worker_id: str
    state: str
    check_in_code: str | None


class TonightShiftResponse(BaseModel):
    shift: ShiftResponse
    workers: list[TonightWorkerResponse]
    missing: int


class VenueOverviewResponse(BaseModel):
    window_start: UtcTimestamp
    days: list[DayCoverageResponse]
    open_seats: int
    pending_applications: PendingApplicationsResponse
    attendance: AttendanceResponse
    tonight: list[TonightShiftResponse]


class WorkerActivityResponse(BaseModel):
    worker_id: str
    completed: int
    last_worked: UtcTimestamp | None
    recently_broken: bool


class RosterActivityResponse(BaseModel):
    workers: list[WorkerActivityResponse]

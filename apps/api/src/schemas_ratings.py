from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class RatingCreateRequest(BaseModel):
    stars: int = Field(ge=1, le=5)
    comment: str | None = None


class WorkerRatingSummaryResponse(BaseModel):
    avg_stars: float | None
    total_ratings: int
    unrated_bookings: list["UnratedBookingResponse"]


class UnratedBookingResponse(BaseModel):
    booking_id: str
    shift_id: str
    start_time: datetime
    role: str
    location: str


class CompletedShiftResponse(BaseModel):
    booking_id: str
    shift_id: str
    worker_id: str
    start_time: datetime
    role: str
    location: str
    operator_rating: int | None = None

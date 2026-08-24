from __future__ import annotations

from pydantic import BaseModel, Field

from apps.api.src.validation_types import UtcTimestamp


class RatingCreateRequest(BaseModel):
    stars: int = Field(ge=1, le=5)
    comment: str | None = Field(default=None, max_length=1000)


class PendingRatingResponse(BaseModel):
    booking_id: str
    shift_id: str
    target_id: str
    target_name: str
    target_avatar_url: str | None = None
    shift_role: str
    shift_location: str
    start_time: UtcTimestamp
    end_time: UtcTimestamp


class WorkerRatingSummaryResponse(BaseModel):
    avg_stars: float | None
    total_ratings: int
    unrated_bookings: list["UnratedBookingResponse"]


class VenueRatingSummaryResponse(BaseModel):
    venue_id: str
    avg_stars: float | None
    total_ratings: int


class UnratedBookingResponse(BaseModel):
    booking_id: str
    shift_id: str
    start_time: UtcTimestamp
    role: str
    location: str


class CompletedShiftResponse(BaseModel):
    booking_id: str
    shift_id: str
    worker_id: str
    start_time: UtcTimestamp
    role: str
    location: str
    operator_rating: int | None = None

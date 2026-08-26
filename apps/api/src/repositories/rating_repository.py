from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol

from apps.api.src.models.rating import Rating


@dataclass(frozen=True)
class UnratedBooking:
    booking_id: str
    shift_id: str
    worker_id: str
    start_time: datetime
    role: str
    location: str


@dataclass(frozen=True)
class PendingRating:
    booking_id: str
    shift_id: str
    target_id: str
    target_name: str
    target_avatar_url: str | None
    shift_role: str
    shift_location: str
    start_time: datetime
    end_time: datetime


class DuplicateRatingError(Exception):
    pass


class RatingRepository(Protocol):
    def save(self, rating: Rating) -> Rating:
        ...

    def get_by_booking_and_role(self, booking_id: str, role: str) -> Rating | None:
        ...

    def avg_operator_rating_for_worker(self, worker_id: str) -> tuple[float | None, int]:
        ...

    def avg_worker_rating_for_venue(self, venue_id: str) -> tuple[float | None, int]:
        ...

    def unrated_bookings_for_operator(self, worker_id: str, account_id: str) -> list[UnratedBooking]:
        ...

    def completed_bookings_for_account(self, account_id: str) -> list[UnratedBooking]:
        ...

    def pending_for_worker(self, worker_id: str, limit: int = 1) -> list[PendingRating]:
        ...

    def pending_for_account(self, account_id: str, limit: int = 1) -> list[PendingRating]:
        ...

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol

from apps.api.src.models.rating import Rating


class UnratedBooking:
    def __init__(self, booking_id: str, shift_id: str, start_time: object, role: str, location: str) -> None:
        self.booking_id = booking_id
        self.shift_id = shift_id
        self.start_time = start_time
        self.role = role
        self.location = location


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
        raise NotImplementedError

    def get_by_booking_and_role(self, booking_id: str, role: str) -> Rating | None:
        raise NotImplementedError

    def avg_operator_rating_for_worker(self, worker_id: str) -> tuple[float | None, int]:
        """Returns (avg_stars, total_count) for operator ratings of this worker."""
        raise NotImplementedError

    def avg_worker_rating_for_venue(self, venue_id: str) -> tuple[float | None, int]:
        raise NotImplementedError

    def unrated_bookings_for_operator(self, worker_id: str, account_id: str) -> list[UnratedBooking]:
        """Completed bookings at this account that the operator hasn't rated yet."""
        raise NotImplementedError

    def completed_bookings_for_account(self, account_id: str) -> list[UnratedBooking]:
        """All checked-out/approved bookings for the operator's account (for completed shifts section)."""
        raise NotImplementedError

    def pending_for_worker(self, worker_id: str, limit: int = 1) -> list[PendingRating]:
        raise NotImplementedError

    def pending_for_account(self, account_id: str, limit: int = 1) -> list[PendingRating]:
        raise NotImplementedError

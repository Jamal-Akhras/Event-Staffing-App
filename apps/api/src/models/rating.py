from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class Rating:
    rating_id: str
    booking_id: str
    rated_by_role: str
    rater_id: str
    stars: int
    comment: str | None
    created_at: datetime

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class FeedRankingAppeal:
    appeal_id: str
    worker_id: str
    shift_id: str
    slate_id: str | None
    reason: str
    created_at: datetime
    reviewed_at: datetime | None = None
    reviewed_by_user_id: str | None = None
    outcome_note: str | None = None

    def __post_init__(self) -> None:
        if (self.reviewed_at is None) != (self.reviewed_by_user_id is None):
            raise ValueError("A reviewed appeal records its time and reviewer together.")

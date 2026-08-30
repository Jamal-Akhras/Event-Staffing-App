from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime


@dataclass(frozen=True)
class PendingSummary:
    count: int
    oldest_created_at: datetime | None


@dataclass(frozen=True)
class AttendanceSummary:
    completed: int
    no_shows: int

    @property
    def total(self) -> int:
        return self.completed + self.no_shows


@dataclass(frozen=True)
class WorkerActivity:
    worker_id: str
    completed: int
    last_worked: datetime | None
    recently_broken: bool


@dataclass(frozen=True)
class DayCoverage:
    day: date
    total_shifts: int
    open_seats: int

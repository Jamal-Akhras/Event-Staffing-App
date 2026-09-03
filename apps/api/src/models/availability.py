from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta
from enum import Enum
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


class AvailabilityExceptionKind(str, Enum):
    AVAILABLE = "available"
    UNAVAILABLE = "unavailable"


class TimeOffStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    DECLINED = "declined"
    WITHDRAWN = "withdrawn"


class WorkerAvailabilityStatus(str, Enum):
    BOOKED = "booked"
    AWAY = "away"
    UNAVAILABLE = "unavailable"
    AVAILABLE = "available"


@dataclass(frozen=True)
class AvailabilityRule:
    rule_id: str
    worker_id: str
    timezone: str
    weekday: int
    start_minute: int
    duration_minutes: int
    effective_from: date
    effective_until: date | None
    created_at: datetime
    updated_at: datetime

    def __post_init__(self) -> None:
        try:
            ZoneInfo(self.timezone)
        except ZoneInfoNotFoundError as exc:
            raise ValueError("Timezone must be a valid IANA timezone.") from exc
        if not 0 <= self.weekday <= 6:
            raise ValueError("Weekday must be between 0 and 6.")
        if not 0 <= self.start_minute <= 1439:
            raise ValueError("Start minute must be between 0 and 1439.")
        if not 1 <= self.duration_minutes <= 1440:
            raise ValueError("Duration must be between 1 and 1440 minutes.")
        if self.effective_until is not None and self.effective_until < self.effective_from:
            raise ValueError("Effective-until date must not precede effective-from date.")


@dataclass(frozen=True)
class AvailabilityException:
    exception_id: str
    worker_id: str
    kind: AvailabilityExceptionKind
    start_time: datetime
    end_time: datetime
    created_at: datetime
    updated_at: datetime
    note: str | None = None

    def __post_init__(self) -> None:
        _validate_interval(self.start_time, self.end_time)


@dataclass(frozen=True)
class TimeOffRequest:
    request_id: str
    worker_id: str
    venue_id: str
    start_time: datetime
    end_time: datetime
    status: TimeOffStatus
    reason: str
    created_at: datetime
    updated_at: datetime
    decided_at: datetime | None = None
    decided_by_user_id: str | None = None

    def __post_init__(self) -> None:
        _validate_interval(self.start_time, self.end_time)
        decided = self.status in (TimeOffStatus.APPROVED, TimeOffStatus.DECLINED)
        has_decision = self.decided_at is not None or self.decided_by_user_id is not None
        if decided and (self.decided_at is None or self.decided_by_user_id is None):
            raise ValueError("A decided request requires its time and actor.")
        if not decided and has_decision:
            raise ValueError("Decision metadata is only valid on approved or declined requests.")


@dataclass(frozen=True)
class AvailabilityEvaluation:
    available: bool
    availability_configured: bool
    reason: str


@dataclass(frozen=True)
class WorkerCurrentStatus:
    worker_id: str
    status: WorkerAvailabilityStatus
    availability_configured: bool


def _validate_interval(start_time: datetime, end_time: datetime) -> None:
    if start_time.tzinfo is None or end_time.tzinfo is None:
        raise ValueError("Availability intervals require timezone-aware timestamps.")
    if end_time <= start_time:
        raise ValueError("Availability interval end must be after its start.")
    if end_time - start_time > timedelta(days=366):
        raise ValueError("Availability intervals cannot exceed 366 days.")

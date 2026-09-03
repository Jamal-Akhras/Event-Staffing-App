from __future__ import annotations

from datetime import datetime
from typing import Protocol

from apps.api.src.models.availability import (
    AvailabilityException,
    AvailabilityRule,
    TimeOffRequest,
    TimeOffStatus,
)


class AvailabilityRuleRepository(Protocol):
    def save(self, rule: AvailabilityRule) -> AvailabilityRule: ...

    def replace_for_worker(
        self, worker_id: str, rules: list[AvailabilityRule]
    ) -> list[AvailabilityRule]: ...

    def list_for_worker(self, worker_id: str) -> list[AvailabilityRule]: ...

    def list_for_workers(self, worker_ids: list[str]) -> list[AvailabilityRule]: ...


class AvailabilityExceptionRepository(Protocol):
    def save(self, exception: AvailabilityException) -> AvailabilityException: ...

    def get(self, exception_id: str) -> AvailabilityException | None: ...

    def delete(self, exception_id: str) -> None: ...

    def list_for_worker(self, worker_id: str) -> list[AvailabilityException]: ...

    def list_overlapping_workers(
        self, worker_ids: list[str], start_time: datetime, end_time: datetime
    ) -> list[AvailabilityException]: ...


class TimeOffRepository(Protocol):
    def save(self, request: TimeOffRequest) -> TimeOffRequest: ...

    def get(self, request_id: str, for_update: bool = False) -> TimeOffRequest | None: ...

    def list_for_worker(self, worker_id: str) -> list[TimeOffRequest]: ...

    def list_for_venue(
        self,
        venue_id: str,
        status: TimeOffStatus | None = None,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
    ) -> list[TimeOffRequest]: ...

    def list_overlapping_workers(
        self,
        worker_ids: list[str],
        start_time: datetime,
        end_time: datetime,
        venue_id: str | None = None,
        statuses: tuple[TimeOffStatus, ...] | None = None,
    ) -> list[TimeOffRequest]: ...

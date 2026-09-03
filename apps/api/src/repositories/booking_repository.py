from __future__ import annotations

from datetime import datetime
from typing import Protocol

from apps.api.src.models.insights import AttendanceSummary, WorkerActivity
from packages.domain.src.booking import Booking
from packages.domain.src.booking_state import BookingState

LIVE_BOOKING_STATES = (
    BookingState.CONFIRMED,
    BookingState.CHECKED_IN,
    BookingState.CHECKED_OUT,
    BookingState.APPROVED,
    BookingState.PAID,
)


class BookingRepository(Protocol):
    def get(self, booking_id: str) -> Booking | None:
        ...

    def save(self, booking: Booking) -> Booking:
        ...

    def list_recent(self, limit: int = 25) -> list[Booking]:
        ...

    def list_by_worker(
        self,
        worker_id: str,
        limit: int | None = None,
        operator_id: str | None = None,
    ) -> list[Booking]:
        ...

    def list_by_operator(
        self,
        operator_id: str,
        limit: int = 25,
        worker_id: str | None = None,
    ) -> list[Booking]:
        ...

    def list_for_account(
        self,
        account_id: str,
        limit: int = 25,
        worker_id: str | None = None,
    ) -> list[Booking]:
        ...

    def list_by_state(self, state: BookingState) -> list[Booking]:
        ...

    def list_by_shift(self, shift_id: str, for_update: bool = False) -> list[Booking]:
        ...

    def list_for_shifts(self, shift_ids: list[str]) -> list[Booking]:
        ...

    def list_live_for_workers(self, worker_ids: list[str], at: datetime) -> list[Booking]:
        ...

    def list_live_overlapping_for_worker(
        self,
        worker_id: str,
        start_time: datetime,
        end_time: datetime,
        venue_id: str | None = None,
    ) -> list[Booking]:
        ...

    def attendance_summary(self, account_id: str, since: datetime, until: datetime) -> AttendanceSummary:
        ...

    def worker_activity(self, account_id: str, broken_since: datetime) -> list[WorkerActivity]:
        ...

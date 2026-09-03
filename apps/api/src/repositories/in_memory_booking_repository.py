from __future__ import annotations

from datetime import datetime
from typing import Dict

from apps.api.src.models.insights import AttendanceSummary, WorkerActivity
from apps.api.src.repositories.booking_repository import LIVE_BOOKING_STATES
from apps.api.src.repositories.shift_repository import ShiftRepository
from packages.domain.src.booking import Booking
from packages.domain.src.booking_state import BookingState

COMPLETED_STATES = (BookingState.CHECKED_OUT, BookingState.APPROVED, BookingState.PAID)
BROKEN_STATES = (BookingState.NO_SHOW, BookingState.CANCELLED_BY_WORKER)


class InMemoryBookingRepository:
    def __init__(self) -> None:
        self._bookings: Dict[str, Booking] = {}
        self._shift_repo: ShiftRepository | None = None

    def attach_shift_repo(self, shift_repo: ShiftRepository) -> None:
        self._shift_repo = shift_repo

    def get(self, booking_id: str) -> Booking | None:
        return self._bookings.get(booking_id)

    def save(self, booking: Booking) -> Booking:
        self._bookings[booking.booking_id] = booking
        return booking

    def list_recent(self, limit: int = 25) -> list[Booking]:
        bookings = list(self._bookings.values())
        bookings.sort(key=lambda item: item.created_at or item.start_time, reverse=True)
        return bookings[:limit]

    def list_by_worker(
        self,
        worker_id: str,
        limit: int | None = None,
        operator_id: str | None = None,
    ) -> list[Booking]:
        return self._list(limit, worker_id=worker_id, operator_id=operator_id)

    def list_by_operator(
        self,
        operator_id: str,
        limit: int = 25,
        worker_id: str | None = None,
    ) -> list[Booking]:
        return self._list(limit, worker_id=worker_id, operator_id=operator_id)

    def list_for_account(
        self,
        account_id: str,
        limit: int = 25,
        worker_id: str | None = None,
    ) -> list[Booking]:
        if self._shift_repo is None:
            raise RuntimeError("InMemoryBookingRepository requires a shift repo to list by account.")
        account_shift_ids = {shift.shift_id for shift in self._shift_repo.list_for_account(account_id, limit=10_000)}
        items = [item for item in self._bookings.values() if item.shift_id in account_shift_ids]
        if worker_id:
            items = [item for item in items if item.worker_id == worker_id]
        items.sort(key=lambda item: item.created_at or item.start_time, reverse=True)
        return items[:limit]

    def list_by_state(self, state: BookingState) -> list[Booking]:
        return [booking for booking in self._bookings.values() if booking.state == state]

    def list_by_shift(self, shift_id: str, for_update: bool = False) -> list[Booking]:
        return [booking for booking in self._bookings.values() if booking.shift_id == shift_id]

    def list_for_shifts(self, shift_ids: list[str]) -> list[Booking]:
        wanted = set(shift_ids)
        items = [booking for booking in self._bookings.values() if booking.shift_id in wanted]
        items.sort(key=lambda item: item.start_time)
        return items

    def list_live_for_workers(self, worker_ids: list[str], at: datetime) -> list[Booking]:
        wanted = set(worker_ids)
        items = [
            booking
            for booking in self._bookings.values()
            if booking.worker_id in wanted
            and booking.state in LIVE_BOOKING_STATES
            and booking.start_time <= at < booking.end_time
        ]
        return sorted(items, key=lambda booking: (booking.start_time, booking.booking_id))

    def list_live_overlapping_for_worker(
        self,
        worker_id: str,
        start_time: datetime,
        end_time: datetime,
        venue_id: str | None = None,
    ) -> list[Booking]:
        if venue_id is not None and self._shift_repo is None:
            raise RuntimeError("InMemoryBookingRepository requires a shift repo for venue filtering.")
        items = [
            booking
            for booking in self._bookings.values()
            if booking.worker_id == worker_id
            and booking.state in LIVE_BOOKING_STATES
            and booking.start_time < end_time
            and booking.end_time > start_time
        ]
        if venue_id is not None:
            venue_shift_ids = {
                shift.shift_id for shift in self._shift_repo.list_for_account(venue_id, limit=10_000)
            }
            items = [booking for booking in items if booking.shift_id in venue_shift_ids]
        return sorted(items, key=lambda booking: (booking.start_time, booking.booking_id))

    def attendance_summary(self, account_id: str, since: datetime, until: datetime) -> AttendanceSummary:
        window = [
            booking
            for booking in self._account_bookings(account_id)
            if since <= booking.start_time <= until
        ]
        return AttendanceSummary(
            completed=sum(1 for booking in window if booking.state in COMPLETED_STATES),
            no_shows=sum(1 for booking in window if booking.state == BookingState.NO_SHOW),
        )

    def worker_activity(self, account_id: str, broken_since: datetime) -> list[WorkerActivity]:
        activity: dict[str, list[Booking]] = {}
        for booking in self._account_bookings(account_id):
            activity.setdefault(booking.worker_id, []).append(booking)
        rows = []
        for worker_id, bookings in activity.items():
            done = [booking for booking in bookings if booking.state in COMPLETED_STATES]
            rows.append(
                WorkerActivity(
                    worker_id=worker_id,
                    completed=len(done),
                    last_worked=max((booking.start_time for booking in done), default=None),
                    recently_broken=any(
                        booking.state in BROKEN_STATES and booking.start_time >= broken_since
                        for booking in bookings
                    ),
                )
            )
        return sorted(rows, key=lambda row: row.worker_id)

    def _account_bookings(self, account_id: str) -> list[Booking]:
        if self._shift_repo is None:
            raise RuntimeError("InMemoryBookingRepository requires a shift repo to aggregate by account.")
        shift_ids = {shift.shift_id for shift in self._shift_repo.list_for_account(account_id, limit=10_000)}
        return [booking for booking in self._bookings.values() if booking.shift_id in shift_ids]

    def clear(self) -> None:
        self._bookings.clear()

    def _list(
        self,
        limit: int | None,
        worker_id: str | None = None,
        operator_id: str | None = None,
    ) -> list[Booking]:
        items = list(self._bookings.values())
        if worker_id:
            items = [item for item in items if item.worker_id == worker_id]
        if operator_id:
            items = [item for item in items if item.operator_id == operator_id]
        items.sort(key=lambda item: item.created_at or item.start_time, reverse=True)
        return items if limit is None else items[:limit]

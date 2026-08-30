from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta

from apps.api.src.models.insights import AttendanceSummary, DayCoverage, PendingSummary, WorkerActivity
from apps.api.src.models.shift import Shift
from apps.api.src.repositories.application_repository import ApplicationRepository
from apps.api.src.repositories.booking_repository import BookingRepository
from apps.api.src.repositories.shift_repository import ShiftRepository
from packages.domain.src.booking import Booking

ATTENDANCE_WINDOW_DAYS = 30
BROKEN_WINDOW_DAYS = 90
ACTIVE_STATES = frozenset(
    {"requested", "confirmed", "checked_in", "checked_out", "approved", "paid"}
)


@dataclass(frozen=True)
class TonightShift:
    shift: Shift
    bookings: list[Booking]


@dataclass(frozen=True)
class VenueOverview:
    window_start: datetime
    days: list[DayCoverage]
    open_seats: int
    pending: PendingSummary
    attendance: AttendanceSummary
    tonight: list[TonightShift]


class VenueInsightsService:
    def __init__(
        self,
        shifts: ShiftRepository,
        bookings: BookingRepository,
        applications: ApplicationRepository,
    ) -> None:
        self._shifts = shifts
        self._bookings = bookings
        self._applications = applications

    def overview(self, account_id: str, window_start: datetime, days: int, now: datetime) -> VenueOverview:
        window_end = window_start + timedelta(days=days)
        shifts = [
            shift
            for shift in self._shifts.list_in_range(account_id, window_start, window_end)
            if shift.status != "cancelled"
        ]
        coverage = _coverage(shifts, window_start, days)
        today = [shift for shift in shifts if window_start <= shift.start_time < window_start + timedelta(days=1)]
        booked = self._bookings.list_for_shifts([shift.shift_id for shift in today])
        return VenueOverview(
            window_start=window_start,
            days=coverage,
            open_seats=sum(day.open_seats for day in coverage),
            pending=self._applications.pending_summary(account_id),
            attendance=self._bookings.attendance_summary(
                account_id, now - timedelta(days=ATTENDANCE_WINDOW_DAYS), now
            ),
            tonight=[
                TonightShift(
                    shift=shift,
                    bookings=[
                        booking
                        for booking in booked
                        if booking.shift_id == shift.shift_id and booking.state.value in ACTIVE_STATES
                    ],
                )
                for shift in today
            ],
        )

    def roster_activity(self, account_id: str, now: datetime) -> list[WorkerActivity]:
        return self._bookings.worker_activity(account_id, now - timedelta(days=BROKEN_WINDOW_DAYS))


def _coverage(shifts: list[Shift], window_start: datetime, days: int) -> list[DayCoverage]:
    buckets: list[list[Shift]] = [[] for _ in range(days)]
    for shift in shifts:
        index = (shift.start_time - window_start).days
        if 0 <= index < days:
            buckets[index].append(shift)
    return [
        DayCoverage(
            day=(window_start + timedelta(days=index)).date(),
            total_shifts=len(bucket),
            open_seats=sum(
                max(shift.workers_needed - shift.workers_filled, 0)
                for shift in bucket
                if shift.status == "open"
            ),
        )
        for index, bucket in enumerate(buckets)
    ]

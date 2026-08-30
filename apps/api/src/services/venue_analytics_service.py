from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from decimal import Decimal

from apps.api.src.models.shift import Shift
from apps.api.src.repositories.application_repository import ApplicationRepository
from apps.api.src.repositories.booking_repository import BookingRepository
from apps.api.src.repositories.shift_repository import ShiftRepository
from apps.api.src.services.billing_math import money, worked_hours
from packages.domain.src.booking_state import BookingState

PERIOD_DAYS = {"week": 7, "month": 30, "quarter": 92}
TREND_BUCKETS = 6
MAX_TREND_DAYS = 184
STAFFED_STATES = frozenset(
    {BookingState.CONFIRMED, BookingState.CHECKED_IN, BookingState.CHECKED_OUT, BookingState.APPROVED, BookingState.PAID}
)


@dataclass(frozen=True)
class Gap:
    shift_id: str
    role: str
    location: str
    start_time: datetime
    unfilled: int
    applications: int
    lead_time_hours: float
    pay_rate: Decimal
    reason: str


@dataclass(frozen=True)
class AnalyticsSummary:
    period: str
    window_start: datetime
    window_end: datetime
    seats_posted: int
    seats_filled: int
    fill_rate: float
    applications: int
    applications_per_seat: float
    hours_staffed: Decimal
    average_pay_rate: Decimal
    currency: str
    fill_rate_trend: list[float] = field(default_factory=list)
    applications_trend: list[float] = field(default_factory=list)
    hours_trend: list[float] = field(default_factory=list)
    rate_trend: list[float] = field(default_factory=list)
    gaps: list[Gap] = field(default_factory=list)
    roles: list[tuple[str, int]] = field(default_factory=list)


class VenueAnalyticsService:
    def __init__(
        self,
        shifts: ShiftRepository,
        bookings: BookingRepository,
        applications: ApplicationRepository,
    ) -> None:
        self._shifts = shifts
        self._bookings = bookings
        self._applications = applications

    def summarise(self, account_id: str, period: str, now: datetime) -> AnalyticsSummary:
        days = PERIOD_DAYS.get(period, PERIOD_DAYS["month"])
        window_start = now - timedelta(days=days)
        trend_span = min(days * TREND_BUCKETS, MAX_TREND_DAYS)
        trend_start = now - timedelta(days=trend_span)

        shifts = [
            shift
            for shift in self._shifts.list_in_range(account_id, trend_start, now)
            if shift.status != "cancelled"
        ]
        shift_ids = [shift.shift_id for shift in shifts]
        bookings = self._bookings.list_for_shifts(shift_ids)
        applications = self._applications.list_for_shifts(shift_ids)

        current = [shift for shift in shifts if shift.start_time >= window_start]
        bucket_size = timedelta(days=trend_span / TREND_BUCKETS)

        return AnalyticsSummary(
            period=period,
            window_start=window_start,
            window_end=now,
            seats_posted=_seats(current),
            seats_filled=_filled(current),
            fill_rate=_rate(_filled(current), _seats(current)),
            applications=len([a for a in applications if a.shift_id in {s.shift_id for s in current}]),
            applications_per_seat=round(
                len([a for a in applications if a.shift_id in {s.shift_id for s in current}])
                / max(_seats(current), 1),
                1,
            ),
            hours_staffed=_hours(bookings, current),
            average_pay_rate=_average_rate(current),
            currency=current[0].currency if current else "GBP",
            fill_rate_trend=_bucket(shifts, trend_start, bucket_size, lambda group: _rate(_filled(group), _seats(group))),
            applications_trend=_bucket(
                shifts,
                trend_start,
                bucket_size,
                lambda group: float(len([a for a in applications if a.shift_id in {s.shift_id for s in group}])),
            ),
            hours_trend=_bucket(shifts, trend_start, bucket_size, lambda group: float(_hours(bookings, group))),
            rate_trend=_bucket(shifts, trend_start, bucket_size, lambda group: float(_average_rate(group))),
            gaps=_gaps(current, applications, now),
            roles=_roles(current),
        )


def _seats(shifts: list[Shift]) -> int:
    return sum(shift.workers_needed for shift in shifts)


def _filled(shifts: list[Shift]) -> int:
    return sum(min(shift.workers_filled, shift.workers_needed) for shift in shifts)


def _rate(filled: int, posted: int) -> float:
    return round(filled / posted * 100, 1) if posted else 0.0


def _hours(bookings, shifts: list[Shift]) -> Decimal:
    wanted = {shift.shift_id for shift in shifts}
    total = sum(
        (worked_hours(booking) for booking in bookings if booking.shift_id in wanted and booking.state in STAFFED_STATES),
        Decimal("0"),
    )
    return money(total)


def _average_rate(shifts: list[Shift]) -> Decimal:
    if not shifts:
        return Decimal("0.00")
    return money(sum((Decimal(shift.pay_rate) for shift in shifts), Decimal("0")) / len(shifts))


def _bucket(shifts: list[Shift], start: datetime, size: timedelta, measure) -> list[float]:
    values = []
    for index in range(TREND_BUCKETS):
        edge = start + size * index
        group = [shift for shift in shifts if edge <= shift.start_time < edge + size]
        values.append(round(measure(group), 2))
    return values


def _roles(shifts: list[Shift]) -> list[tuple[str, int]]:
    counts: dict[str, int] = {}
    for shift in shifts:
        counts[shift.role] = counts.get(shift.role, 0) + shift.workers_needed
    return sorted(counts.items(), key=lambda item: item[1], reverse=True)


def _gaps(shifts: list[Shift], applications, now: datetime) -> list[Gap]:
    venue_average = _average_rate(shifts)
    per_shift: dict[str, int] = {}
    for application in applications:
        per_shift[application.shift_id] = per_shift.get(application.shift_id, 0) + 1

    gaps = []
    for shift in shifts:
        unfilled = shift.workers_needed - shift.workers_filled
        if unfilled <= 0 or shift.start_time > now:
            continue
        applied = per_shift.get(shift.shift_id, 0)
        lead = (shift.start_time - shift.created_at).total_seconds() / 3600
        gaps.append(
            Gap(
                shift_id=shift.shift_id,
                role=shift.role,
                location=shift.location,
                start_time=shift.start_time,
                unfilled=unfilled,
                applications=applied,
                lead_time_hours=round(lead, 1),
                pay_rate=money(Decimal(shift.pay_rate)),
                reason=_reason(applied, shift.workers_needed, lead, Decimal(shift.pay_rate), venue_average),
            )
        )
    return sorted(gaps, key=lambda gap: gap.unfilled, reverse=True)


def _reason(applications: int, seats: int, lead_hours: float, rate: Decimal, venue_average: Decimal) -> str:
    per_seat = applications / max(seats, 1)
    if lead_hours < 1:
        return "Posted less than an hour ahead"
    if lead_hours < 12:
        return f"Posted {round(lead_hours)} hours ahead"
    if per_seat < 2:
        return f"{round(per_seat, 1)} applications per seat"
    if venue_average and rate < venue_average - Decimal("1"):
        return f"£{venue_average - rate:.2f} below your average rate"
    return "Applicants withdrew or were declined"

from __future__ import annotations

from datetime import UTC, date, datetime, time, timedelta
from zoneinfo import ZoneInfo

from apps.api.src.models.availability import (
    AvailabilityEvaluation,
    AvailabilityException,
    AvailabilityExceptionKind,
    AvailabilityRule,
    TimeOffStatus,
    WorkerAvailabilityStatus,
    WorkerCurrentStatus,
)
from apps.api.src.repositories.availability_repository import (
    AvailabilityExceptionRepository,
    AvailabilityRuleRepository,
    TimeOffRepository,
)
from apps.api.src.repositories.booking_repository import BookingRepository


class AvailabilityService:
    def __init__(
        self,
        rules: AvailabilityRuleRepository,
        exceptions: AvailabilityExceptionRepository,
        time_off: TimeOffRepository,
        bookings: BookingRepository,
    ) -> None:
        self._rules = rules
        self._exceptions = exceptions
        self._time_off = time_off
        self._bookings = bookings

    def evaluate_interval(
        self, worker_id: str, start_time: datetime, end_time: datetime
    ) -> AvailabilityEvaluation:
        rules = self._rules.list_for_worker(worker_id)
        exceptions = self._exceptions.list_overlapping_workers(
            [worker_id], start_time, end_time
        )
        return evaluate_availability_interval(rules, exceptions, start_time, end_time)

    def current_statuses(
        self, venue_id: str, worker_ids: list[str], at: datetime
    ) -> dict[str, WorkerCurrentStatus]:
        if not worker_ids:
            return {}
        _require_aware(at)
        point_end = at + timedelta(microseconds=1)
        rules = self._rules.list_for_workers(worker_ids)
        exceptions = self._exceptions.list_overlapping_workers(worker_ids, at, point_end)
        time_off = self._time_off.list_overlapping_workers(
            worker_ids,
            at,
            point_end,
            venue_id=venue_id,
            statuses=(TimeOffStatus.APPROVED,),
        )
        booked_workers = {
            booking.worker_id for booking in self._bookings.list_live_for_workers(worker_ids, at)
        }
        away_workers = {request.worker_id for request in time_off}
        return {
            worker_id: self._current_status(
                worker_id,
                at,
                rules,
                exceptions,
                worker_id in booked_workers,
                worker_id in away_workers,
            )
            for worker_id in worker_ids
        }

    @staticmethod
    def _current_status(
        worker_id: str,
        at: datetime,
        rules: list[AvailabilityRule],
        exceptions: list[AvailabilityException],
        booked: bool,
        away: bool,
    ) -> WorkerCurrentStatus:
        worker_rules = [rule for rule in rules if rule.worker_id == worker_id]
        worker_exceptions = [item for item in exceptions if item.worker_id == worker_id]
        evaluation = evaluate_availability_interval(
            worker_rules,
            worker_exceptions,
            at,
            at + timedelta(microseconds=1),
        )
        if booked:
            status = WorkerAvailabilityStatus.BOOKED
        elif away:
            status = WorkerAvailabilityStatus.AWAY
        elif not evaluation.available:
            status = WorkerAvailabilityStatus.UNAVAILABLE
        else:
            status = WorkerAvailabilityStatus.AVAILABLE
        return WorkerCurrentStatus(worker_id, status, evaluation.availability_configured)


def evaluate_availability_interval(
    rules: list[AvailabilityRule],
    exceptions: list[AvailabilityException],
    start_time: datetime,
    end_time: datetime,
) -> AvailabilityEvaluation:
    _validate_interval(start_time, end_time)
    configured = bool(rules)
    overlapping = [
        item
        for item in exceptions
        if item.start_time < end_time and item.end_time > start_time
    ]
    if any(item.kind == AvailabilityExceptionKind.UNAVAILABLE for item in overlapping):
        return AvailabilityEvaluation(False, configured, "unavailable_exception")
    available_exceptions = [
        (item.start_time.astimezone(UTC), item.end_time.astimezone(UTC))
        for item in overlapping
        if item.kind == AvailabilityExceptionKind.AVAILABLE
    ]
    recurring = recurring_utc_intervals(rules, start_time, end_time)
    if _covers_interval(recurring + available_exceptions, start_time, end_time):
        if available_exceptions and recurring:
            reason = "combined"
        elif available_exceptions:
            reason = "available_exception"
        else:
            reason = "recurring_rule"
        return AvailabilityEvaluation(True, configured, reason)
    if not configured:
        return AvailabilityEvaluation(True, False, "not_configured")
    return AvailabilityEvaluation(False, True, "outside_recurring_rules")


def recurring_utc_intervals(
    rules: list[AvailabilityRule], start_time: datetime, end_time: datetime
) -> list[tuple[datetime, datetime]]:
    _validate_interval(start_time, end_time)
    intervals: list[tuple[datetime, datetime]] = []
    for rule in rules:
        zone = ZoneInfo(rule.timezone)
        first_day = start_time.astimezone(zone).date() - timedelta(days=1)
        last_day = end_time.astimezone(zone).date()
        for local_day in _dates_between(first_day, last_day):
            if local_day.weekday() != rule.weekday:
                continue
            if local_day < rule.effective_from:
                continue
            if rule.effective_until is not None and local_day > rule.effective_until:
                continue
            local_start = datetime.combine(local_day, time.min, zone) + timedelta(
                minutes=rule.start_minute
            )
            local_end = local_start + timedelta(minutes=rule.duration_minutes)
            utc_window = (local_start.astimezone(UTC), local_end.astimezone(UTC))
            if utc_window[0] < end_time and utc_window[1] > start_time:
                intervals.append(utc_window)
    return intervals


def _dates_between(first_day: date, last_day: date):
    day = first_day
    while day <= last_day:
        yield day
        day += timedelta(days=1)


def _covers_interval(
    intervals: list[tuple[datetime, datetime]], start_time: datetime, end_time: datetime
) -> bool:
    cursor = start_time.astimezone(UTC)
    target_end = end_time.astimezone(UTC)
    for interval_start, interval_end in sorted(intervals):
        interval_start = interval_start.astimezone(UTC)
        interval_end = interval_end.astimezone(UTC)
        if interval_end <= cursor:
            continue
        if interval_start > cursor:
            return False
        cursor = max(cursor, interval_end)
        if cursor >= target_end:
            return True
    return False


def _validate_interval(start_time: datetime, end_time: datetime) -> None:
    _require_aware(start_time)
    _require_aware(end_time)
    if end_time <= start_time:
        raise ValueError("Availability interval end must be after its start.")


def _require_aware(value: datetime) -> None:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("Availability evaluation requires timezone-aware timestamps.")

from __future__ import annotations

from datetime import UTC, date, datetime, timedelta

import pytest

from apps.api.src.models.availability import (
    AvailabilityException,
    AvailabilityExceptionKind,
    AvailabilityRule,
)
from apps.api.src.services.availability_service import (
    evaluate_availability_interval,
    recurring_utc_intervals,
)

CREATED = datetime(2026, 1, 1, tzinfo=UTC)


def _rule(
    weekday: int,
    start_minute: int,
    duration_minutes: int,
    timezone: str = "Europe/London",
) -> AvailabilityRule:
    return AvailabilityRule(
        rule_id="rule-1",
        worker_id="worker-1",
        timezone=timezone,
        weekday=weekday,
        start_minute=start_minute,
        duration_minutes=duration_minutes,
        effective_from=date(2026, 1, 1),
        effective_until=None,
        created_at=CREATED,
        updated_at=CREATED,
    )


def _exception(
    kind: AvailabilityExceptionKind, start_time: datetime, end_time: datetime
) -> AvailabilityException:
    return AvailabilityException(
        exception_id=f"exception-{kind.value}",
        worker_id="worker-1",
        kind=kind,
        start_time=start_time,
        end_time=end_time,
        created_at=CREATED,
        updated_at=CREATED,
    )


@pytest.mark.parametrize(
    ("rule", "start_time", "end_time", "expected_window"),
    [
        (
            _rule(0, 22 * 60, 8 * 60),
            datetime(2026, 2, 3, 1, tzinfo=UTC),
            datetime(2026, 2, 3, 5, tzinfo=UTC),
            (datetime(2026, 2, 2, 22, tzinfo=UTC), datetime(2026, 2, 3, 6, tzinfo=UTC)),
        ),
        (
            _rule(6, 0, 4 * 60),
            datetime(2026, 3, 29, 0, tzinfo=UTC),
            datetime(2026, 3, 29, 3, tzinfo=UTC),
            (datetime(2026, 3, 29, 0, tzinfo=UTC), datetime(2026, 3, 29, 3, tzinfo=UTC)),
        ),
        (
            _rule(6, 0, 4 * 60),
            datetime(2026, 10, 24, 23, tzinfo=UTC),
            datetime(2026, 10, 25, 4, tzinfo=UTC),
            (datetime(2026, 10, 24, 23, tzinfo=UTC), datetime(2026, 10, 25, 4, tzinfo=UTC)),
        ),
    ],
    ids=["overnight", "spring-forward", "fall-back"],
)
def test_recurring_windows_are_evaluated_in_local_wall_time(
    rule, start_time, end_time, expected_window
):
    assert recurring_utc_intervals([rule], start_time, end_time) == [expected_window]
    assert evaluate_availability_interval([rule], [], start_time, end_time).available is True


def test_an_overnight_rule_does_not_cover_time_after_its_end():
    evaluation = evaluate_availability_interval(
        [_rule(0, 22 * 60, 8 * 60)],
        [],
        datetime(2026, 2, 3, 5, tzinfo=UTC),
        datetime(2026, 2, 3, 7, tzinfo=UTC),
    )

    assert evaluation.available is False
    assert evaluation.reason == "outside_recurring_rules"


@pytest.mark.parametrize(
    ("exceptions", "expected_available", "expected_reason"),
    [
        ([AvailabilityExceptionKind.AVAILABLE], True, "available_exception"),
        ([AvailabilityExceptionKind.UNAVAILABLE], False, "unavailable_exception"),
        (
            [AvailabilityExceptionKind.AVAILABLE, AvailabilityExceptionKind.UNAVAILABLE],
            False,
            "unavailable_exception",
        ),
    ],
)
def test_exception_precedence(exceptions, expected_available, expected_reason):
    start_time = datetime(2026, 2, 2, 18, tzinfo=UTC)
    end_time = start_time + timedelta(hours=1)
    evaluation = evaluate_availability_interval(
        [_rule(0, 9 * 60, 8 * 60)],
        [_exception(kind, start_time, end_time) for kind in exceptions],
        start_time,
        end_time,
    )

    assert evaluation.available is expected_available
    assert evaluation.reason == expected_reason
    assert evaluation.availability_configured is True


def test_no_recurring_rules_preserves_manual_work_with_unconfigured_status():
    start_time = datetime(2026, 2, 2, 18, tzinfo=UTC)
    evaluation = evaluate_availability_interval(
        [], [], start_time, start_time + timedelta(hours=1)
    )

    assert evaluation.available is True
    assert evaluation.availability_configured is False
    assert evaluation.reason == "not_configured"


def test_an_available_exception_must_cover_the_whole_requested_interval():
    start_time = datetime(2026, 2, 2, 18, tzinfo=UTC)
    evaluation = evaluate_availability_interval(
        [_rule(0, 9 * 60, 8 * 60)],
        [_exception(AvailabilityExceptionKind.AVAILABLE, start_time, start_time + timedelta(minutes=30))],
        start_time,
        start_time + timedelta(hours=1),
    )

    assert evaluation.available is False

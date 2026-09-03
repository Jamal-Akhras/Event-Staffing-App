from datetime import UTC, date, datetime, timedelta

import pytest
from sqlalchemy.exc import IntegrityError

from apps.api.src.db.availability_models import (
    AvailabilityExceptionModel,
    AvailabilityRuleModel,
    TimeOffRequestModel,
)
from apps.api.tests.test_availability_repository_roundtrip import _seed_worker_and_venue

NOW = datetime(2030, 6, 3, 9, tzinfo=UTC)


def test_database_rejects_an_invalid_availability_rule(repo_session):
    _seed_worker_and_venue(repo_session)
    repo_session.add(
        AvailabilityRuleModel(
            rule_id="bad-rule",
            worker_id="worker-availability",
            timezone="Europe/London",
            weekday=7,
            start_minute=540,
            duration_minutes=480,
            effective_from=date(2030, 6, 1),
            created_at=NOW,
            updated_at=NOW,
        )
    )
    with pytest.raises(IntegrityError):
        repo_session.flush()


@pytest.mark.parametrize(
    ("start_time", "end_time"),
    [
        (NOW + timedelta(days=2), NOW + timedelta(days=1)),
        (NOW, NOW + timedelta(days=367)),
    ],
)
def test_database_rejects_invalid_exception_intervals(repo_session, start_time, end_time):
    _seed_worker_and_venue(repo_session)
    repo_session.add(
        AvailabilityExceptionModel(
            exception_id="bad-exception",
            worker_id="worker-availability",
            kind="available",
            start_time=start_time,
            end_time=end_time,
            created_at=NOW,
            updated_at=NOW,
        )
    )
    with pytest.raises(IntegrityError):
        repo_session.flush()


def test_database_rejects_incomplete_time_off_decision_metadata(repo_session):
    _seed_worker_and_venue(repo_session)
    repo_session.add(
        TimeOffRequestModel(
            request_id="bad-time-off",
            worker_id="worker-availability",
            venue_id="venue-availability",
            start_time=NOW + timedelta(days=2),
            end_time=NOW + timedelta(days=3),
            status="approved",
            reason="Holiday",
            created_at=NOW,
            updated_at=NOW,
        )
    )
    with pytest.raises(IntegrityError):
        repo_session.flush()

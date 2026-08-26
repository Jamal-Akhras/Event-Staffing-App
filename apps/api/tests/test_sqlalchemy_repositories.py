from datetime import UTC, datetime, timedelta

import pytest

from apps.api.src.db.models import BookingModel, ShiftModel
from apps.api.src.models.application import Application
from apps.api.src.models.shift import Shift
from apps.api.src.models.user import User
from apps.api.src.models.worker_profile import WorkerProfile
from apps.api.src.repositories.application_repository import DuplicateApplicationError
from apps.api.src.repositories.sqlalchemy_application_decision_repository import (
    SqlAlchemyApplicationDecisionRepository,
)
from apps.api.src.repositories.sqlalchemy_application_repository import (
    SqlAlchemyApplicationRepository,
)
from apps.api.src.repositories.sqlalchemy_shift_repository import SqlAlchemyShiftRepository
from apps.api.src.repositories.sqlalchemy_user_repository import SqlAlchemyUserRepository
from apps.api.src.repositories.sqlalchemy_worker_profile_repository import (
    SqlAlchemyWorkerProfileRepository,
)


def test_sqlalchemy_user_repository_email_lookup_is_case_insensitive(repo_session):
    repo = SqlAlchemyUserRepository(repo_session)
    now = datetime(2030, 1, 1, 8, 0, 0, tzinfo=UTC)
    repo.save(User(
        user_id="operator-email-case",
        email="Venue@Temp.com",
        hashed_password="hashed-password",
        role="operator",
        account_id=None,
        worker_profile_id=None,
        is_active=True,
        created_at=now,
        updated_at=now,
    ))

    loaded = repo.get_by_email("VENUE@TEMP.COM")

    assert loaded is not None
    assert loaded.user_id == "operator-email-case"


def test_sqlalchemy_shift_repository_round_trip(repo_session):
    session = repo_session
    repo = SqlAlchemyShiftRepository(session)
    now = datetime(2030, 1, 1, 9, 0, 0, tzinfo=UTC)
    shift = Shift(
        shift_id="shift-1",
        operator_id="operator-1",
        role="server",
        location="Downtown",
        start_time=now,
        end_time=now + timedelta(hours=4),
        pay_rate=25.0,
        notes="Bring black shirt",
        status="open",
        created_at=now,
        updated_at=now,
        workers_needed=1,
        workers_filled=0,
    )

    repo.save(shift)
    loaded = repo.get("shift-1")
    assert loaded == shift


def test_sqlalchemy_application_repository_round_trip(repo_session):
    session = repo_session
    repo = SqlAlchemyApplicationRepository(session)
    shift_repo = SqlAlchemyShiftRepository(session)
    now = datetime(2030, 1, 1, 10, 0, 0, tzinfo=UTC)
    shift_repo.save(
        Shift(
            shift_id="shift-1",
            operator_id="operator-1",
            role="server",
            location="Downtown",
            start_time=now,
            end_time=now + timedelta(hours=4),
            pay_rate=25.0,
            notes=None,
            status="open",
            created_at=now,
            workers_needed=1,
            workers_filled=0,
        )
    )
    application = Application(
        application_id="app-1",
        shift_id="shift-1",
        worker_id="worker-1",
        operator_id="operator-1",
        start_time=now,
        end_time=now + timedelta(hours=4),
        message="Ready to help.",
        booking_id=None,
        status="applied",
        created_at=now,
    )

    repo.save(application)
    loaded = repo.get("app-1")
    assert loaded == application


def test_sqlalchemy_worker_profile_repository_round_trip(repo_session):
    session = repo_session
    repo = SqlAlchemyWorkerProfileRepository(session)
    now = datetime(2030, 1, 1, 8, 0, 0, tzinfo=UTC)
    profile = WorkerProfile(
        worker_id="worker-1",
        display_name="Alex Worker",
        role="server",
        city="Austin",
        experience_years=3,
        reliability_score=0.75,
        badges=["fast"],
        bio="Reliable and punctual.",
        languages=["en"],
        email="alex@example.com",
        phone="555-0100",
        address="100 Main St",
        emergency_contact="555-0101",
        pay_rate=25.0,
        notes="Prefers evening shifts.",
        updated_at=now,
    )

    repo.save(profile)
    loaded = repo.get("worker-1")
    assert loaded == profile


def test_sqlalchemy_application_repository_rejects_duplicate_worker_shift(repo_session):
    session = repo_session
    shift_repo = SqlAlchemyShiftRepository(session)
    repo = SqlAlchemyApplicationRepository(session)
    now = datetime(2030, 1, 1, 10, 0, 0, tzinfo=UTC)
    shift_repo.save(_shift("shift-1", now, workers_needed=2))
    repo.save(_application("app-1", "worker-1", now))

    with pytest.raises(DuplicateApplicationError):
        repo.save(_application("app-2", "worker-1", now))


def test_sqlalchemy_application_decision_approve_is_single_write_path(repo_session):
    session = repo_session
    shift_repo = SqlAlchemyShiftRepository(session)
    application_repo = SqlAlchemyApplicationRepository(session)
    decision_repo = SqlAlchemyApplicationDecisionRepository(session)
    now = datetime(2030, 1, 1, 10, 0, 0, tzinfo=UTC)
    shift_repo.save(_shift("shift-1", now))
    application_repo.save(_application("app-1", "worker-1", now))

    result = decision_repo.approve("app-1", now + timedelta(minutes=5), "booking-1")

    assert result.application.status == "approved"
    assert result.application.booking_id == "booking-1"
    assert session.get(BookingModel, "booking-1") is not None
    stored_shift = session.get(ShiftModel, "shift-1")
    assert stored_shift.workers_filled == 1
    assert stored_shift.status == "filled"


def _shift(shift_id: str, now: datetime, workers_needed: int = 1) -> Shift:
    return Shift(
        shift_id=shift_id,
        operator_id="operator-1",
        role="server",
        location="Downtown",
        start_time=now,
        end_time=now + timedelta(hours=4),
        pay_rate=25.0,
        notes=None,
        status="open",
        created_at=now,
        workers_needed=workers_needed,
        workers_filled=0,
    )


def _application(application_id: str, worker_id: str, now: datetime) -> Application:
    return Application(
        application_id=application_id,
        shift_id="shift-1",
        worker_id=worker_id,
        operator_id="operator-1",
        start_time=now,
        end_time=now + timedelta(hours=4),
        message="Ready to help.",
        booking_id=None,
        status="applied",
        created_at=now,
    )

from datetime import datetime, timedelta

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from apps.api.src.db.database import Base
from apps.api.src.db import models
from apps.api.src.models.application import Application
from apps.api.src.models.shift import Shift
from apps.api.src.models.worker_profile import WorkerProfile
from apps.api.src.repositories.sqlalchemy_application_repository import (
    SqlAlchemyApplicationRepository,
)
from apps.api.src.repositories.sqlalchemy_shift_repository import SqlAlchemyShiftRepository
from apps.api.src.repositories.sqlalchemy_worker_profile_repository import (
    SqlAlchemyWorkerProfileRepository,
)


def _session():
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    models  # ensure models are registered
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)()


def test_sqlalchemy_shift_repository_round_trip():
    session = _session()
    repo = SqlAlchemyShiftRepository(session)
    now = datetime(2030, 1, 1, 9, 0, 0)
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
    )

    repo.save(shift)
    loaded = repo.get("shift-1")
    assert loaded == shift


def test_sqlalchemy_application_repository_round_trip():
    session = _session()
    repo = SqlAlchemyApplicationRepository(session)
    now = datetime(2030, 1, 1, 10, 0, 0)
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


def test_sqlalchemy_worker_profile_repository_round_trip():
    session = _session()
    repo = SqlAlchemyWorkerProfileRepository(session)
    now = datetime(2030, 1, 1, 8, 0, 0)
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

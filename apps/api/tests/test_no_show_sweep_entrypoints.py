from __future__ import annotations

from datetime import UTC, datetime, timedelta

from apps.api.src.models.worker_profile import WorkerProfile
from apps.api.src.repositories.in_memory_booking_repository import InMemoryBookingRepository
from apps.api.src.repositories.in_memory_shift_repository import InMemoryShiftRepository
from apps.api.src.repositories.in_memory_worker_profile_repository import (
    InMemoryWorkerProfileRepository,
)
from packages.domain.src.booking import Booking
from packages.domain.src.booking_state import BookingState


class _DummySession:
    def close(self) -> None:
        pass

    def commit(self) -> None:
        pass


def _seed_confirmed_no_show(now: datetime):
    booking_repo = InMemoryBookingRepository()
    worker_repo = InMemoryWorkerProfileRepository()
    shift_repo = InMemoryShiftRepository()
    start_time = now - timedelta(hours=1)

    booking_repo.save(
        Booking(
            booking_id="booking-1",
            shift_id="shift-1",
            worker_id="worker-1",
            operator_id="operator-1",
            start_time=start_time,
            end_time=start_time + timedelta(hours=4),
            state=BookingState.CONFIRMED,
            created_at=now - timedelta(days=1),
            confirmed_at=now - timedelta(days=1),
        )
    )
    worker_repo.save(
        WorkerProfile(
            worker_id="worker-1",
            display_name="Alex Worker",
            role="server",
            city="Austin",
            experience_years=3,
            reliability_score=1.0,
            badges=[],
            bio=None,
            languages=["en"],
            email=None,
            phone=None,
            address=None,
            emergency_contact=None,
            pay_rate=None,
            notes=None,
            updated_at=now - timedelta(days=1),
        )
    )
    return booking_repo, worker_repo, shift_repo


def test_scheduler_run_no_show_sweep_end_to_end(monkeypatch):
    from apps.api.src import scheduler
    from apps.api.src.repositories import (
        sqlalchemy_booking_repository,
        sqlalchemy_shift_repository,
        sqlalchemy_worker_profile_repository,
    )
    from apps.api.src.db import database

    booking_repo, worker_repo, shift_repo = _seed_confirmed_no_show(datetime.now(UTC))

    monkeypatch.setattr(database, "SessionLocal", lambda: _DummySession())
    monkeypatch.setattr(
        sqlalchemy_booking_repository, "SqlAlchemyBookingRepository", lambda session: booking_repo
    )
    monkeypatch.setattr(
        sqlalchemy_worker_profile_repository,
        "SqlAlchemyWorkerProfileRepository",
        lambda session: worker_repo,
    )
    monkeypatch.setattr(
        sqlalchemy_shift_repository, "SqlAlchemyShiftRepository", lambda session: shift_repo
    )

    scheduler.run_no_show_sweep()

    refreshed = booking_repo.get("booking-1")
    assert refreshed is not None
    assert refreshed.state == BookingState.NO_SHOW


def test_job_run_no_show_sweep_end_to_end(monkeypatch):
    from apps.api.src.jobs import run_no_show_sweep as job

    now = datetime.now(UTC)
    booking_repo, worker_repo, shift_repo = _seed_confirmed_no_show(now)

    monkeypatch.setattr(job, "SessionLocal", lambda: _DummySession())
    monkeypatch.setattr(job, "SqlAlchemyBookingRepository", lambda session: booking_repo)
    monkeypatch.setattr(job, "SqlAlchemyWorkerProfileRepository", lambda session: worker_repo)
    monkeypatch.setattr(job, "SqlAlchemyShiftRepository", lambda session: shift_repo)

    count = job.run(now)

    assert count == 1
    refreshed = booking_repo.get("booking-1")
    assert refreshed is not None
    assert refreshed.state == BookingState.NO_SHOW

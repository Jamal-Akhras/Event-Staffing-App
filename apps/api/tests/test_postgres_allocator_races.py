from __future__ import annotations

import threading
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from sqlalchemy import func, select

from apps.api.src.db.models import BookingModel, ShiftModel
from apps.api.src.repositories.booking_allocator import AllocationError
from apps.api.src.repositories.sqlalchemy_booking_allocator import SqlAlchemyBookingAllocator

pytestmark = pytest.mark.postgres

NOW = datetime(2030, 6, 1, 9, 0, tzinfo=UTC)
START = NOW + timedelta(days=7)


def _session_factory():
    from apps.api.src.db.database import SessionLocal

    return SessionLocal


def _seed_shift(shift_id: str, start: datetime, workers_needed: int = 1) -> None:
    SessionLocal = _session_factory()
    with SessionLocal() as session, session.begin():
        session.add(
            ShiftModel(
                shift_id=shift_id,
                operator_id="operator-1",
                role="server",
                location="Bath",
                start_time=start,
                end_time=start + timedelta(hours=5),
                pay_rate=15.5,
                status="open",
                created_at=NOW,
                workers_needed=workers_needed,
                workers_filled=0,
            )
        )


def _allocate_concurrently(jobs: list[tuple[str, str]]) -> list[str]:
    SessionLocal = _session_factory()
    barrier = threading.Barrier(len(jobs))
    outcomes: list[str] = []
    lock = threading.Lock()

    def allocate(shift_id: str, worker_id: str) -> None:
        session = SessionLocal()
        allocator = SqlAlchemyBookingAllocator(session)
        barrier.wait(timeout=10)
        try:
            with session.begin():
                allocator.allocate(shift_id, worker_id, NOW, str(uuid4()))
            outcome = "booked"
        except AllocationError as exc:
            outcome = type(exc).__name__
        finally:
            session.close()
        with lock:
            outcomes.append(outcome)

    threads = [threading.Thread(target=allocate, args=job) for job in jobs]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=30)
    assert all(not thread.is_alive() for thread in threads), "allocator threads deadlocked"
    return outcomes


def _booking_count(where) -> int:
    SessionLocal = _session_factory()
    with SessionLocal() as session:
        return session.execute(select(func.count()).select_from(BookingModel).where(where)).scalar_one()


def test_two_workers_racing_the_last_seat_yield_exactly_one_booking():
    shift_id = f"race-seat-{uuid4().hex[:8]}"
    _seed_shift(shift_id, START)

    outcomes = _allocate_concurrently([(shift_id, "seat-worker-1"), (shift_id, "seat-worker-2")])

    assert sorted(outcomes) == ["ShiftFullError", "booked"]
    assert _booking_count(BookingModel.shift_id == shift_id) == 1


def test_one_worker_racing_two_overlapping_shifts_lands_exactly_once():
    worker_id = f"overlap-worker-{uuid4().hex[:8]}"
    first = f"race-a-{uuid4().hex[:8]}"
    second = f"race-b-{uuid4().hex[:8]}"
    _seed_shift(first, START)
    _seed_shift(second, START + timedelta(hours=2))

    outcomes = _allocate_concurrently([(first, worker_id), (second, worker_id)])

    assert sorted(outcomes) == ["OverlappingBookingError", "booked"]
    assert _booking_count(BookingModel.worker_id == worker_id) == 1

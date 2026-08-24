from __future__ import annotations

import threading
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from sqlalchemy import func, select

from apps.api.src.db.models import ApplicationModel, BookingModel, ShiftModel
from apps.api.src.repositories.application_decision_repository import (
    ApplicationAlreadyDecidedError,
    ShiftAlreadyFullError,
)
from apps.api.src.repositories.sqlalchemy_application_decision_repository import (
    SqlAlchemyApplicationDecisionRepository,
)

pytestmark = pytest.mark.postgres

NOW = datetime(2030, 1, 1, 9, 0, 0, tzinfo=UTC)


def _session_factory():
    from apps.api.src.db.database import SessionLocal

    return SessionLocal


def _seed_shift_with_applications(application_ids: list[str], workers_needed: int = 1) -> str:
    SessionLocal = _session_factory()
    shift_id = str(uuid4())
    with SessionLocal() as session, session.begin():
        session.add(
            ShiftModel(
                shift_id=shift_id,
                operator_id="operator-1",
                role="server",
                location="Bath",
                start_time=NOW + timedelta(hours=2),
                end_time=NOW + timedelta(hours=6),
                pay_rate=15.5,
                status="open",
                created_at=NOW,
                workers_needed=workers_needed,
                workers_filled=0,
            )
        )
        session.flush()
        for index, application_id in enumerate(application_ids):
            session.add(
                ApplicationModel(
                    application_id=application_id,
                    shift_id=shift_id,
                    worker_id=f"worker-{index}",
                    operator_id="operator-1",
                    start_time=NOW + timedelta(hours=2),
                    end_time=NOW + timedelta(hours=6),
                    status="applied",
                    created_at=NOW,
                )
            )
    return shift_id


def _approve_concurrently(application_ids: list[str]) -> list[tuple[str, str]]:
    SessionLocal = _session_factory()
    barrier = threading.Barrier(len(application_ids))
    outcomes: list[tuple[str, str]] = []
    lock = threading.Lock()

    def approve(application_id: str) -> None:
        session = SessionLocal()
        repo = SqlAlchemyApplicationDecisionRepository(session)
        barrier.wait(timeout=10)
        try:
            with session.begin():
                repo.approve(application_id, NOW + timedelta(hours=1), str(uuid4()))
            outcome = ("approved", application_id)
        except (ShiftAlreadyFullError, ApplicationAlreadyDecidedError) as exc:
            outcome = ("refused", type(exc).__name__)
        finally:
            session.close()
        with lock:
            outcomes.append(outcome)

    threads = [
        threading.Thread(target=approve, args=(application_id,))
        for application_id in application_ids
    ]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=30)
    assert all(not thread.is_alive() for thread in threads), "approval threads deadlocked"
    return outcomes


def _shift_state(shift_id: str) -> tuple[int, str, int]:
    SessionLocal = _session_factory()
    with SessionLocal() as session:
        shift = session.get(ShiftModel, shift_id)
        booking_count = session.execute(
            select(func.count()).select_from(BookingModel).where(BookingModel.shift_id == shift_id)
        ).scalar_one()
        return shift.workers_filled, shift.status, booking_count


def test_concurrent_approvals_cannot_overfill_last_slot():
    application_ids = [str(uuid4()), str(uuid4())]
    shift_id = _seed_shift_with_applications(application_ids, workers_needed=1)

    outcomes = _approve_concurrently(application_ids)

    assert sorted(result for result, _ in outcomes) == ["approved", "refused"]
    refused = next(detail for result, detail in outcomes if result == "refused")
    assert refused == "ShiftAlreadyFullError"

    workers_filled, status, booking_count = _shift_state(shift_id)
    assert workers_filled == 1
    assert status == "filled"
    assert booking_count == 1


def test_same_application_cannot_be_approved_twice_concurrently():
    application_id = str(uuid4())
    shift_id = _seed_shift_with_applications([application_id], workers_needed=2)

    outcomes = _approve_concurrently([application_id, application_id])

    assert sorted(result for result, _ in outcomes) == ["approved", "refused"]
    refused = next(detail for result, detail in outcomes if result == "refused")
    assert refused == "ApplicationAlreadyDecidedError"

    workers_filled, status, booking_count = _shift_state(shift_id)
    assert workers_filled == 1
    assert status == "open"
    assert booking_count == 1

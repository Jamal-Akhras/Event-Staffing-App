from __future__ import annotations

import threading
from datetime import UTC, datetime
from uuid import uuid4

import pytest
from sqlalchemy import func, select

from apps.api.src.db.tenancy_models import OrganisationModel, VenueModel
from apps.api.src.db.workforce_models import VenueJoinCodeModel, VenueJoinCodeRedemptionModel, WorkerRelationshipModel
from apps.api.src.repositories.sqlalchemy_account_repository import SqlAlchemyAccountRepository
from apps.api.src.repositories.sqlalchemy_venue_join_code_repository import SqlAlchemyVenueJoinCodeRepository
from apps.api.src.repositories.sqlalchemy_worker_profile_repository import SqlAlchemyWorkerProfileRepository
from apps.api.src.repositories.sqlalchemy_worker_relationship_repository import (
    SqlAlchemyRelationshipTransitionRepository,
    SqlAlchemyWorkerRelationshipRepository,
)
from apps.api.src.services.errors import ServiceError
from apps.api.src.services.join_code_service import JoinCodeService
from apps.api.src.services.relationship_service import RelationshipService

pytestmark = pytest.mark.postgres

NOW = datetime(2030, 1, 1, 9, 0, 0, tzinfo=UTC)
VENUE_ID = "race-venue"


def _session_factory():
    from apps.api.src.db.database import SessionLocal

    return SessionLocal


def _seed_code_with_one_slot() -> str:
    SessionLocal = _session_factory()
    code = f"TEAM-RACE-{uuid4().hex[:4].upper()}"
    with SessionLocal() as session, session.begin():
        session.add(
            OrganisationModel(
                organisation_id="race-org", name="Race Group", country="GB", currency="GBP", created_at=NOW
            )
        )
        session.add(
            VenueModel(
                venue_id=VENUE_ID,
                organisation_id="race-org",
                name="Race Venue",
                country="GB",
                currency="GBP",
                created_at=NOW,
            )
        )
        session.add(
            VenueJoinCodeModel(
                code=code,
                venue_id=VENUE_ID,
                default_relationship_type="permanent",
                max_redemptions=1,
                created_at=NOW,
                created_by_user_id="operator-1",
            )
        )
    return code


def _redeem_concurrently(code: str, worker_ids: list[str]) -> list[tuple[str, str]]:
    SessionLocal = _session_factory()
    barrier = threading.Barrier(len(worker_ids))
    outcomes: list[tuple[str, str]] = []
    lock = threading.Lock()

    def redeem(worker_id: str) -> None:
        session = SessionLocal()
        service = JoinCodeService(
            SqlAlchemyVenueJoinCodeRepository(session),
            RelationshipService(
                SqlAlchemyWorkerRelationshipRepository(session),
                SqlAlchemyRelationshipTransitionRepository(session),
                SqlAlchemyWorkerProfileRepository(session),
            ),
            SqlAlchemyAccountRepository(session),
        )
        barrier.wait(timeout=10)
        try:
            with session.begin():
                service.redeem(code, worker_id, NOW)
            outcome = ("redeemed", worker_id)
        except ServiceError as exc:
            outcome = ("refused", str(exc))
        finally:
            session.close()
        with lock:
            outcomes.append(outcome)

    threads = [threading.Thread(target=redeem, args=(worker_id,)) for worker_id in worker_ids]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=30)
    assert all(not thread.is_alive() for thread in threads), "redeem threads deadlocked"
    return outcomes


def test_the_final_slot_admits_exactly_one_worker_and_leaves_the_loser_clean():
    code = _seed_code_with_one_slot()
    outcomes = _redeem_concurrently(code, ["race-worker-1", "race-worker-2"])

    assert sorted(result for result, _ in outcomes) == ["redeemed", "refused"]
    winner = next(detail for result, detail in outcomes if result == "redeemed")
    loser = "race-worker-2" if winner == "race-worker-1" else "race-worker-1"

    SessionLocal = _session_factory()
    with SessionLocal() as session:
        redemptions = session.execute(
            select(func.count()).select_from(VenueJoinCodeRedemptionModel).where(
                VenueJoinCodeRedemptionModel.code == code
            )
        ).scalar_one()
        relationships = session.execute(
            select(WorkerRelationshipModel.worker_id).where(WorkerRelationshipModel.venue_id == VENUE_ID)
        ).scalars().all()

    assert redemptions == 1
    assert relationships == [winner]
    assert loser not in relationships

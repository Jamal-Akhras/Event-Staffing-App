from __future__ import annotations

import threading
from datetime import UTC, date, datetime
from uuid import uuid4

import pytest
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError

from apps.api.src.db.rota_models import RotaPublicationModel
from apps.api.src.db.tenancy_models import OrganisationModel, VenueModel
from apps.api.src.models.rota_publication import RotaPublication
from apps.api.src.repositories.sqlalchemy_rota_publication_repository import (
    SqlAlchemyRotaPublicationRepository,
)

pytestmark = pytest.mark.postgres

NOW = datetime(2030, 6, 3, 9, 0, tzinfo=UTC)
WEEK = date(2030, 6, 10)


def _session_factory():
    from apps.api.src.db.database import SessionLocal

    return SessionLocal


def _seed_venue(venue_id: str) -> None:
    SessionLocal = _session_factory()
    with SessionLocal() as session, session.begin():
        session.add(
            OrganisationModel(
                organisation_id=f"org-{venue_id}", name="Race", country="GB", currency="GBP", created_at=NOW
            )
        )
        session.add(
            VenueModel(
                venue_id=venue_id,
                organisation_id=f"org-{venue_id}",
                name="Race Venue",
                country="GB",
                currency="GBP",
                created_at=NOW,
            )
        )


def test_concurrent_publishes_of_the_same_week_mint_one_revision():
    venue_id = f"rota-race-{uuid4().hex[:8]}"
    _seed_venue(venue_id)
    SessionLocal = _session_factory()
    barrier = threading.Barrier(2)
    outcomes: list[str] = []
    lock = threading.Lock()

    def publish() -> None:
        session = SessionLocal()
        repo = SqlAlchemyRotaPublicationRepository(session)
        publication = RotaPublication(
            publication_id=str(uuid4()),
            venue_id=venue_id,
            week_start=WEEK,
            revision=1,
            published_at=NOW,
            published_by_user_id="operator-1",
            assignments=[],
        )
        barrier.wait(timeout=10)
        try:
            with session.begin():
                repo.save(publication)
            outcome = "saved"
        except IntegrityError:
            outcome = "conflict"
        finally:
            session.close()
        with lock:
            outcomes.append(outcome)

    threads = [threading.Thread(target=publish) for _ in range(2)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=30)
    assert all(not thread.is_alive() for thread in threads), "publish threads deadlocked"

    assert sorted(outcomes) == ["conflict", "saved"]
    with SessionLocal() as session:
        count = session.execute(
            select(func.count()).select_from(RotaPublicationModel).where(
                RotaPublicationModel.venue_id == venue_id
            )
        ).scalar_one()
    assert count == 1

from datetime import UTC, datetime
from decimal import Decimal

from apps.api.src.models.worker_profile import WorkerProfile
from apps.api.src.repositories.sqlalchemy_worker_profile_repository import (
    SqlAlchemyWorkerProfileRepository,
)


def test_every_worker_profile_field_survives_a_sql_round_trip(repo_session):
    repo = SqlAlchemyWorkerProfileRepository(repo_session)
    saved = WorkerProfile(
        worker_id="worker-profile-roundtrip",
        display_name="Morgan Lee",
        role="Chef",
        city="Bath",
        experience_years=8,
        reliability_score=0.97,
        badges=["top-rated", "returning"],
        bio="Evening service specialist",
        languages=["English", "French"],
        email="morgan@example.com",
        phone="07000000001",
        address="12 Test Street",
        emergency_contact="Casey 07000000002",
        pay_rate=Decimal("18.75"),
        notes="Allergy training complete",
        updated_at=datetime(2030, 6, 3, 9, tzinfo=UTC),
        avatar_url="https://example.com/avatar.jpg",
        allow_venue_recontact=True,
        market_id=None,
        marketplace_enabled=False,
    )
    repo.save(saved)
    repo_session.expunge_all()

    assert repo.get(saved.worker_id) == saved

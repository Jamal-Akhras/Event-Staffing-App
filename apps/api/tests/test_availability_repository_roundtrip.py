from datetime import UTC, date, datetime, timedelta

from apps.api.src.db.tenancy_models import OrganisationModel, VenueModel
from apps.api.src.models.availability import (
    AvailabilityException,
    AvailabilityExceptionKind,
    AvailabilityRule,
    TimeOffRequest,
    TimeOffStatus,
)
from apps.api.src.models.worker_profile import WorkerProfile
from apps.api.src.repositories.sqlalchemy_availability_repository import (
    SqlAlchemyAvailabilityExceptionRepository,
    SqlAlchemyAvailabilityRuleRepository,
    SqlAlchemyTimeOffRepository,
)
from apps.api.src.repositories.sqlalchemy_worker_profile_repository import (
    SqlAlchemyWorkerProfileRepository,
)

NOW = datetime(2030, 6, 3, 9, tzinfo=UTC)


def _seed_worker_and_venue(session) -> None:
    session.add(
        OrganisationModel(
            organisation_id="org-availability",
            name="Availability Group",
            country="GB",
            currency="GBP",
            created_at=NOW,
        )
    )
    session.add(
        VenueModel(
            venue_id="venue-availability",
            organisation_id="org-availability",
            name="Availability Venue",
            country="GB",
            currency="GBP",
            created_at=NOW,
        )
    )
    SqlAlchemyWorkerProfileRepository(session).save(
        WorkerProfile(
            worker_id="worker-availability",
            display_name="Alex",
            role="Bartender",
            city="Bath",
            experience_years=3,
            reliability_score=0.95,
            badges=["reliable"],
            bio="Available evenings",
            languages=["English"],
            email="alex@example.com",
            phone="07000000000",
            address="Bath",
            emergency_contact="Sam",
            pay_rate=15,
            notes="Prefers bar work",
            updated_at=NOW,
            marketplace_enabled=False,
        )
    )
    session.flush()


def test_every_availability_rule_field_survives_a_sql_round_trip(repo_session):
    _seed_worker_and_venue(repo_session)
    repo = SqlAlchemyAvailabilityRuleRepository(repo_session)
    saved = AvailabilityRule(
        rule_id="rule-roundtrip",
        worker_id="worker-availability",
        timezone="Europe/London",
        weekday=4,
        start_minute=17 * 60 + 30,
        duration_minutes=420,
        effective_from=date(2030, 6, 1),
        effective_until=date(2030, 12, 31),
        created_at=NOW,
        updated_at=NOW + timedelta(minutes=1),
    )
    repo.save(saved)
    repo_session.expunge_all()

    assert repo.list_for_worker("worker-availability") == [saved]


def test_every_availability_exception_field_survives_a_sql_round_trip(repo_session):
    _seed_worker_and_venue(repo_session)
    repo = SqlAlchemyAvailabilityExceptionRepository(repo_session)
    saved = AvailabilityException(
        exception_id="exception-roundtrip",
        worker_id="worker-availability",
        kind=AvailabilityExceptionKind.UNAVAILABLE,
        start_time=NOW + timedelta(days=2),
        end_time=NOW + timedelta(days=2, hours=4),
        note="Appointment",
        created_at=NOW,
        updated_at=NOW + timedelta(minutes=1),
    )
    repo.save(saved)
    repo_session.expunge_all()

    assert repo.get(saved.exception_id) == saved


def test_every_time_off_field_survives_a_sql_round_trip(repo_session):
    _seed_worker_and_venue(repo_session)
    repo = SqlAlchemyTimeOffRepository(repo_session)
    saved = TimeOffRequest(
        request_id="time-off-roundtrip",
        worker_id="worker-availability",
        venue_id="venue-availability",
        start_time=NOW + timedelta(days=7),
        end_time=NOW + timedelta(days=10),
        status=TimeOffStatus.APPROVED,
        reason="Holiday",
        created_at=NOW,
        updated_at=NOW + timedelta(minutes=2),
        decided_at=NOW + timedelta(minutes=2),
        decided_by_user_id="manager-1",
    )
    repo.save(saved)
    repo_session.expunge_all()

    assert repo.get(saved.request_id) == saved

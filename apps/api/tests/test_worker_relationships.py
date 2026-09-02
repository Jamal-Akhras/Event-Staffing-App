from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from apps.api.src.models.venue_join_code import VenueJoinCode, VenueJoinCodeRedemption
from apps.api.src.models.worker_relationship import RelationshipTransition, WorkerRelationship
from apps.api.src.repositories.in_memory_venue_join_code_repository import InMemoryVenueJoinCodeRepository
from apps.api.src.repositories.in_memory_worker_relationship_repository import (
    InMemoryRelationshipTransitionRepository,
    InMemoryWorkerRelationshipRepository,
)
from apps.api.src.repositories.sqlalchemy_venue_join_code_repository import SqlAlchemyVenueJoinCodeRepository
from apps.api.src.repositories.sqlalchemy_worker_relationship_repository import (
    SqlAlchemyRelationshipTransitionRepository,
    SqlAlchemyWorkerRelationshipRepository,
)

NOW = datetime(2030, 5, 1, 9, 0, tzinfo=UTC)
VENUE = "venue-1"


def _relationship(worker_id: str, relationship_type: str = "permanent", **overrides) -> WorkerRelationship:
    values = dict(
        relationship_id=f"rel-{worker_id}",
        venue_id=VENUE,
        worker_id=worker_id,
        relationship_type=relationship_type,
        status="active",
        created_at=NOW,
        updated_at=NOW,
        default_role="Bartender",
        start_date=NOW,
        contracted_hours_per_week=Decimal("30.00"),
        agreed_rate=Decimal("13.50"),
        created_by_user_id="operator-1",
    )
    values.update(overrides)
    return WorkerRelationship(**values)


@pytest.fixture()
def seeded_session(repo_session):
    from apps.api.src.db.tenancy_models import OrganisationModel, VenueModel

    repo_session.add(
        OrganisationModel(
            organisation_id="org-1",
            name="Test Group",
            country="GB",
            currency="GBP",
            created_at=NOW,
        )
    )
    for venue_id in (VENUE, "venue-2"):
        repo_session.add(
            VenueModel(
                venue_id=venue_id,
                organisation_id="org-1",
                name=venue_id,
                country="GB",
                currency="GBP",
                created_at=NOW,
            )
        )
    repo_session.flush()
    return repo_session


@pytest.fixture(params=["memory", "database"])
def backend(request, seeded_session):
    if request.param == "memory":
        return {
            "relationships": InMemoryWorkerRelationshipRepository(),
            "transitions": InMemoryRelationshipTransitionRepository(),
            "join_codes": InMemoryVenueJoinCodeRepository(),
        }
    return {
        "relationships": SqlAlchemyWorkerRelationshipRepository(seeded_session),
        "transitions": SqlAlchemyRelationshipTransitionRepository(seeded_session),
        "join_codes": SqlAlchemyVenueJoinCodeRepository(seeded_session),
    }


@pytest.fixture()
def relationships(backend):
    return backend["relationships"]


@pytest.fixture()
def transitions(backend):
    return backend["transitions"]


def test_relationship_round_trips_every_field(relationships):
    saved = relationships.save(_relationship("worker-1"))
    loaded = relationships.get(saved.relationship_id)
    assert loaded == saved


def test_one_relationship_per_venue_and_worker(relationships):
    relationships.save(_relationship("worker-1", "pool"))
    relationships.save(_relationship("worker-1", "permanent"))
    assert len(relationships.list_for_venue(VENUE)) == 1
    assert relationships.get_for_venue_worker(VENUE, "worker-1").relationship_type == "permanent"


def test_venue_listing_separates_team_pool_and_one_off(relationships):
    relationships.save(_relationship("worker-1", "permanent"))
    relationships.save(_relationship("worker-2", "pool"))
    relationships.save(_relationship("worker-3", "one_off", status="ended"))
    everyone = relationships.list_for_venue(VENUE)
    assert {item.relationship_type for item in everyone} == {"permanent", "pool", "one_off"}
    assert [item.worker_id for item in relationships.list_for_venue(VENUE, status="ended")] == ["worker-3"]


def test_a_worker_holds_relationships_with_several_venues(relationships):
    relationships.save(_relationship("worker-1", "permanent"))
    relationships.save(_relationship("worker-1", "pool", relationship_id="rel-other", venue_id="venue-2"))
    assert len(relationships.list_for_worker("worker-1")) == 2


def test_transitions_are_append_only_and_ordered(relationships, transitions):
    relationship = relationships.save(_relationship("worker-1", "one_off"))
    for index, (from_type, to_type) in enumerate([("one_off", "pool"), ("pool", "permanent")]):
        transitions.record(
            RelationshipTransition(
                transition_id=f"trn-{index}",
                relationship_id=relationship.relationship_id,
                from_relationship_type=from_type,
                to_relationship_type=to_type,
                from_status="active",
                to_status="active",
                occurred_at=NOW + timedelta(days=index),
                actor_user_id="operator-1",
                reason="promoted",
            )
        )
    recorded = transitions.list_for_relationship(relationship.relationship_id)
    assert [item.to_relationship_type for item in recorded] == ["pool", "permanent"]


@pytest.fixture()
def join_codes(backend):
    return backend["join_codes"]


def _code(code: str = "BATH-TEAM-01", max_redemptions: int = 2) -> VenueJoinCode:
    return VenueJoinCode(
        code=code,
        venue_id=VENUE,
        default_relationship_type="permanent",
        max_redemptions=max_redemptions,
        created_at=NOW,
        created_by_user_id="operator-1",
        default_role="Bartender",
        expires_at=NOW + timedelta(days=30),
    )


def test_join_code_round_trips(join_codes):
    saved = join_codes.save_code(_code())
    assert join_codes.get_code(saved.code) == saved
    assert join_codes.list_codes_for_venue(VENUE) == [saved]


def test_redemptions_are_counted_per_code(join_codes, relationships):
    code = join_codes.save_code(_code())
    for index in range(2):
        worker_id = f"worker-{index}"
        relationship = relationships.save(_relationship(worker_id))
        join_codes.save_redemption(
            VenueJoinCodeRedemption(
                redemption_id=f"red-{index}",
                code=code.code,
                venue_id=VENUE,
                worker_id=worker_id,
                relationship_id=relationship.relationship_id,
                redeemed_at=NOW,
            )
        )
    assert join_codes.count_redemptions(code.code) == 2
    assert len(join_codes.list_redemptions(code.code)) == 2

from datetime import UTC, datetime
from decimal import Decimal

import pytest

from apps.api.src.models.worker_relationship import RelationshipTransition, WorkerRelationship
from apps.api.src.repositories.in_memory_worker_relationship_repository import (
    InMemoryRelationshipTransitionRepository,
    InMemoryWorkerRelationshipRepository,
)
from apps.api.src.repositories.in_memory_organisation_repository import (
    InMemoryOrganisationRepository,
)
from apps.api.src.services.charge_recorder import ChargeRecorder

CREATED = datetime(2030, 3, 1, tzinfo=UTC)
INVITED = datetime(2030, 3, 10, tzinfo=UTC)
START = datetime(2030, 3, 12, 18, 0, tzinfo=UTC)
ACCEPTED = datetime(2030, 3, 14, tzinfo=UTC)
LATER = datetime(2030, 3, 15, 18, 0, tzinfo=UTC)


@pytest.fixture()
def repos():
    return InMemoryWorkerRelationshipRepository(), InMemoryRelationshipTransitionRepository()


def _recorder(relationships, transitions) -> ChargeRecorder:
    from apps.api.src.repositories.in_memory_commercial_repository import (
        InMemoryCommercialAgreementRepository,
    )

    return ChargeRecorder(
        None, None, None, None, Decimal("8.00"), relationships, transitions,
        InMemoryOrganisationRepository(), InMemoryCommercialAgreementRepository(),
    )


def _relationship(repo, relationship_type: str, status: str, created_at: datetime = CREATED):
    repo.save(
        WorkerRelationship(
            relationship_id="rel-1",
            venue_id="venue-1",
            worker_id="worker-1",
            relationship_type=relationship_type,
            status=status,
            created_at=created_at,
            updated_at=created_at,
        )
    )


def _transition(
    repo, occurred_at: datetime, to_type: str, to_status: str,
    from_type: str | None = None, from_status: str | None = None,
):
    repo.record(
        RelationshipTransition(
            transition_id=f"t-{occurred_at.isoformat()}",
            relationship_id="rel-1",
            to_relationship_type=to_type,
            to_status=to_status,
            occurred_at=occurred_at,
            from_relationship_type=from_type,
            from_status=from_status,
        )
    )


def _as_of(repos, at: datetime) -> str:
    relationships, transitions = repos
    return _recorder(relationships, transitions)._relationship_as_of("venue-1", "worker-1", at)


def test_no_relationship_reconstructs_as_one_off(repos):
    assert _as_of(repos, START) == "one_off"


def test_a_bare_active_row_uses_its_current_type(repos):
    _relationship(repos[0], "pool", "active")
    assert _as_of(repos, START) == "pool"


def test_a_bare_invited_row_keeps_its_standing(repos):
    _relationship(repos[0], "pool", "invited")
    assert _as_of(repos, START) == "pool"


def test_a_bare_row_created_after_the_start_is_one_off(repos):
    _relationship(repos[0], "pool", "active", created_at=ACCEPTED)
    assert _as_of(repos, START) == "one_off"


def test_a_bare_ended_row_is_one_off(repos):
    _relationship(repos[0], "permanent", "ended")
    assert _as_of(repos, START) == "one_off"


def test_a_pool_member_promoted_after_the_shift_reconstructs_as_pool(repos):
    _relationship(repos[0], "permanent", "active")
    _transition(repos[1], CREATED, "pool", "active")
    _transition(repos[1], INVITED, "permanent", "invited", "pool", "active")
    _transition(repos[1], ACCEPTED, "permanent", "active", "permanent", "invited")
    assert _as_of(repos, START) == "pool"
    assert _as_of(repos, LATER) == "permanent"


def test_a_pending_invitation_never_changes_standing(repos):
    _relationship(repos[0], "permanent", "invited")
    _transition(repos[1], CREATED, "pool", "active")
    _transition(repos[1], INVITED, "permanent", "invited", "pool", "active")
    assert _as_of(repos, START) == "pool"


def test_an_employee_offboarded_before_the_shift_is_one_off(repos):
    _relationship(repos[0], "permanent", "ended")
    _transition(repos[1], CREATED, "permanent", "active")
    _transition(repos[1], INVITED, "permanent", "ended", "permanent", "active")
    assert _as_of(repos, START) == "one_off"
    assert _as_of(repos, datetime(2030, 3, 5, tzinfo=UTC)) == "permanent"


def test_a_relationship_whose_history_starts_after_the_shift_is_one_off(repos):
    _relationship(repos[0], "pool", "active", created_at=ACCEPTED)
    _transition(repos[1], ACCEPTED, "pool", "active")
    assert _as_of(repos, START) == "one_off"

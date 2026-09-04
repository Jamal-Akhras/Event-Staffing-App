from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from apps.api.src.models.auto_accept import AutoAcceptAttempt, WorkerAutoAcceptRule
from apps.api.src.models.shift_offer import ShiftOffer
from apps.api.src.repositories.auto_accept_repository import (
    DuplicateAutoAcceptAttemptError,
)
from apps.api.src.repositories.sqlalchemy_auto_accept_repository import (
    SqlAlchemyAutoAcceptAttemptRepository,
    SqlAlchemyWorkerAutoAcceptRuleRepository,
)
from apps.api.src.repositories.sqlalchemy_shift_offer_repository import (
    SqlAlchemyShiftOfferRepository,
)

NOW = datetime(2030, 6, 3, 9, 0, tzinfo=UTC)
START = NOW + timedelta(days=7)


def _seed_offer(repo_session, offer_id: str = "offer-1", worker_id: str = "worker-1") -> None:
    from apps.api.src.db.models import ShiftModel
    from apps.api.src.db.tenancy_models import OrganisationModel, VenueModel

    if repo_session.get(VenueModel, "venue-1") is None:
        repo_session.add(
            OrganisationModel(
                organisation_id="org-1",
                name="Org",
                country="GB",
                currency="GBP",
                created_at=NOW,
            )
        )
        repo_session.flush()
        repo_session.add(
            VenueModel(
                venue_id="venue-1",
                organisation_id="org-1",
                name="Venue",
                country="GB",
                currency="GBP",
                created_at=NOW,
            )
        )
        repo_session.flush()
    shift_id = f"shift-{offer_id}"
    repo_session.add(
        ShiftModel(
            shift_id=shift_id,
            operator_id="operator-1",
            venue_id="venue-1",
            role="Bartender",
            location="Main bar",
            start_time=START,
            end_time=START + timedelta(hours=5),
            pay_rate=Decimal("14.50"),
            status="open",
            created_at=NOW,
            workers_needed=1,
            workers_filled=0,
            currency="GBP",
            origin="assigned",
            assigned_worker_id=worker_id,
            rota_state="published",
        )
    )
    repo_session.flush()
    SqlAlchemyShiftOfferRepository(repo_session).save(
        ShiftOffer(
            offer_id=offer_id,
            shift_id=shift_id,
            venue_id="venue-1",
            worker_id=worker_id,
            source="rota",
            status="pending",
            offered_at=NOW,
            expires_at=START,
        )
    )


def _rule(**overrides) -> WorkerAutoAcceptRule:
    values = dict(
        rule_id="rule-1",
        worker_id="worker-1",
        venue_id="venue-1",
        enabled=True,
        roles=["Bartender", "Server"],
        minimum_rate=Decimal("13.75"),
        minimum_notice_hours=18,
        version=3,
        created_at=NOW,
        updated_at=NOW + timedelta(hours=1),
    )
    values.update(overrides)
    return WorkerAutoAcceptRule(**values)


def _attempt(attempt_id: str, **overrides) -> AutoAcceptAttempt:
    values = dict(
        attempt_id=attempt_id,
        offer_id="offer-1",
        rule_id="rule-1",
        rule_version=3,
        rule_snapshot={
            "enabled": True,
            "roles": ["Bartender", "Server"],
            "minimum_rate": "13.75",
            "minimum_notice_hours": 18,
            "version": 3,
        },
        evaluated_at=NOW + timedelta(minutes=5),
        outcome="skipped",
        reason="role_mismatch",
    )
    values.update(overrides)
    return AutoAcceptAttempt(**values)


def test_every_rule_field_survives_a_sql_round_trip(repo_session):
    _seed_offer(repo_session)
    repo = SqlAlchemyWorkerAutoAcceptRuleRepository(repo_session)
    saved = _rule()
    repo.save(saved)
    repo_session.expunge_all()

    assert repo.get("worker-1", "venue-1") == saved
    assert repo.list_for_worker("worker-1") == [saved]


def test_rule_upsert_and_delete_use_the_worker_venue_key(repo_session):
    _seed_offer(repo_session)
    repo = SqlAlchemyWorkerAutoAcceptRuleRepository(repo_session)
    repo.save(_rule())
    updated = _rule(enabled=False, roles=[], minimum_rate=None, version=4)
    repo.save(updated)

    assert repo.get("worker-1", "venue-1") == updated
    assert repo.delete("worker-1", "venue-1") is True
    assert repo.delete("worker-1", "venue-1") is False


def test_every_attempt_field_survives_a_sql_round_trip(repo_session):
    _seed_offer(repo_session)
    saved = _attempt("attempt-1")
    repo = SqlAlchemyAutoAcceptAttemptRepository(repo_session)
    repo.save(saved)
    repo_session.expunge_all()

    assert repo.get_for_offer_version("offer-1", 3) == saved
    assert repo.list_for_worker("worker-1", 25) == [saved]
    assert repo.list_for_worker("worker-2", 25) == []


def test_database_enforces_one_attempt_per_offer_and_rule_version(repo_session):
    _seed_offer(repo_session)
    repo = SqlAlchemyAutoAcceptAttemptRepository(repo_session)
    saved = _attempt("attempt-1")
    repo.save(saved)

    with pytest.raises(DuplicateAutoAcceptAttemptError):
        repo.save(_attempt("attempt-2", outcome="failed", reason="shift full"))

    assert repo.get_for_offer_version("offer-1", 3) == saved
    repo.save(_attempt("attempt-3", rule_version=4))
    assert repo.get_for_offer_version("offer-1", 4).attempt_id == "attempt-3"

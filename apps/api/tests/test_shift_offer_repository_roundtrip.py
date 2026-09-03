from datetime import UTC, datetime, timedelta

import pytest

from apps.api.src.models.shift_offer import ShiftOffer
from apps.api.src.repositories.shift_offer_repository import DuplicatePendingOfferError
from apps.api.src.repositories.sqlalchemy_shift_offer_repository import (
    SqlAlchemyShiftOfferRepository,
)

NOW = datetime(2030, 6, 3, 9, 0, tzinfo=UTC)


def _offer(offer_id: str, **overrides) -> ShiftOffer:
    values = dict(
        offer_id=offer_id,
        shift_id="shift-1",
        venue_id="venue-1",
        worker_id="worker-1",
        source="rota",
        status="pending",
        offered_at=NOW,
        expires_at=NOW + timedelta(hours=24),
    )
    values.update(overrides)
    return ShiftOffer(**values)


def _seed_shift(repo_session) -> None:
    from apps.api.src.db.tenancy_models import OrganisationModel, VenueModel
    from apps.api.src.db.models import ShiftModel

    repo_session.add(OrganisationModel(organisation_id="org-1", name="Org", country="GB", currency="GBP", created_at=NOW))
    repo_session.flush()
    repo_session.add(
        VenueModel(
            venue_id="venue-1", organisation_id="org-1", name="V", country="GB",
            currency="GBP", created_at=NOW,
        )
    )
    repo_session.flush()
    repo_session.add(
        ShiftModel(
            shift_id="shift-1", operator_id="operator-1", venue_id="venue-1", role="Bartender",
            location="Main bar", start_time=NOW + timedelta(days=7),
            end_time=NOW + timedelta(days=7, hours=5), pay_rate=14.50, status="open",
            created_at=NOW, workers_needed=1, workers_filled=0, currency="GBP",
        )
    )
    repo_session.flush()


def test_every_offer_field_survives_a_sql_round_trip(repo_session):
    _seed_shift(repo_session)
    repo = SqlAlchemyShiftOfferRepository(repo_session)
    saved = _offer(
        "offer-rt-1",
        status="accepted",
        responded_at=NOW + timedelta(hours=2),
        response_source="auto",
    )
    repo.save(saved)
    repo_session.flush()
    repo_session.expunge_all()

    assert repo.get("offer-rt-1") == saved


def test_the_database_enforces_one_pending_offer_per_shift(repo_session):
    _seed_shift(repo_session)
    repo = SqlAlchemyShiftOfferRepository(repo_session)
    repo.save(_offer("offer-1"))

    with pytest.raises(DuplicatePendingOfferError):
        repo.save(_offer("offer-2"))

    repo.save(_offer("offer-1", status="declined", responded_at=NOW, expires_at=None))
    repo.save(_offer("offer-3", worker_id="worker-2"))
    assert repo.get_pending_for_shift("shift-1").offer_id == "offer-3"

from datetime import UTC, datetime, timedelta

import pytest

from apps.api.src.models.shift_change_request import ShiftChangeRequest, ShiftChangeTransition
from apps.api.src.repositories.shift_change_request_repository import DuplicatePendingChangeError
from apps.api.src.repositories.sqlalchemy_booking_repository import SqlAlchemyBookingRepository
from apps.api.src.repositories.sqlalchemy_shift_change_request_repository import (
    SqlAlchemyShiftChangeRequestRepository,
    SqlAlchemyShiftChangeTransitionRepository,
)
from packages.domain.src.booking import Booking
from packages.domain.src.booking_state import BookingState

NOW = datetime(2030, 6, 3, 9, 0, tzinfo=UTC)
START = NOW + timedelta(days=7)


def _seed(repo_session, booking_id: str = "booking-1") -> None:
    from apps.api.src.db.models import ShiftModel
    from apps.api.src.db.tenancy_models import OrganisationModel, VenueModel

    if repo_session.get(VenueModel, "venue-1") is None:
        repo_session.add(
            OrganisationModel(
                organisation_id="org-1", name="Org", country="GB", currency="GBP", created_at=NOW
            )
        )
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
                shift_id="shift-1", operator_id="operator-1", venue_id="venue-1",
                role="Bartender", location="Main bar", start_time=START,
                end_time=START + timedelta(hours=5), pay_rate=14.50, status="open",
                created_at=NOW, workers_needed=2, workers_filled=0, currency="GBP",
            )
        )
        repo_session.flush()
    SqlAlchemyBookingRepository(repo_session).save(
        Booking(
            booking_id=booking_id,
            shift_id="shift-1",
            worker_id="worker-1",
            operator_id="operator-1",
            start_time=START,
            end_time=START + timedelta(hours=5),
            state=BookingState.CONFIRMED,
            created_at=NOW,
            confirmed_at=NOW,
        )
    )
    repo_session.flush()


def _request(request_id: str, **overrides) -> ShiftChangeRequest:
    values = dict(
        request_id=request_id,
        booking_id="booking-1",
        shift_id="shift-1",
        venue_id="venue-1",
        worker_id="worker-1",
        change_type="cover",
        status="pending_replacement",
        reason="Need someone to take this one.",
        replacement_worker_id="worker-2",
        created_at=NOW,
        updated_at=NOW,
    )
    values.update(overrides)
    return ShiftChangeRequest(**values)


def test_every_request_field_survives_a_sql_round_trip(repo_session):
    _seed(repo_session)
    repo = SqlAlchemyShiftChangeRequestRepository(repo_session)
    saved = _request(
        "req-rt-1",
        status="approved",
        decided_at=NOW + timedelta(hours=3),
        decided_by_user_id="user-9",
        updated_at=NOW + timedelta(hours=3),
    )
    repo.save(saved)
    repo_session.flush()
    repo_session.expunge_all()

    assert repo.get("req-rt-1") == saved


def test_every_transition_field_survives_a_sql_round_trip(repo_session):
    _seed(repo_session)
    requests = SqlAlchemyShiftChangeRequestRepository(repo_session)
    requests.save(_request("req-rt-2"))
    repo = SqlAlchemyShiftChangeTransitionRepository(repo_session)
    saved = ShiftChangeTransition(
        transition_id="tr-rt-1",
        request_id="req-rt-2",
        from_status="pending_replacement",
        to_status="pending_manager",
        occurred_at=NOW + timedelta(hours=1),
        actor_user_id="worker-2",
        actor_role="worker",
        note="Replacement accepted.",
    )
    repo.append(saved)
    repo_session.flush()
    repo_session.expunge_all()

    assert repo.list_for_request("req-rt-2") == [saved]


def test_the_database_enforces_one_open_request_per_booking(repo_session):
    _seed(repo_session)
    repo = SqlAlchemyShiftChangeRequestRepository(repo_session)
    repo.save(_request("req-1"))

    with pytest.raises(DuplicatePendingChangeError):
        repo.save(_request("req-2", status="pending_manager"))

    repo.save(_request("req-1", status="withdrawn", updated_at=NOW + timedelta(hours=1)))
    repo.save(_request("req-3", change_type="release", replacement_worker_id=None,
                       status="pending_manager"))
    assert repo.get_pending_for_booking("booking-1").request_id == "req-3"


def test_a_failed_save_rolls_back_cleanly_leaving_the_booking_live(repo_session):
    _seed(repo_session)
    repo = SqlAlchemyShiftChangeRequestRepository(repo_session)
    repo.save(_request("req-1"))

    with pytest.raises(DuplicatePendingChangeError):
        repo.save(_request("req-dup"))

    bookings = SqlAlchemyBookingRepository(repo_session)
    assert bookings.get("booking-1").state == BookingState.CONFIRMED
    assert repo.get("req-dup") is None
    assert repo.get_pending_for_booking("booking-1").request_id == "req-1"

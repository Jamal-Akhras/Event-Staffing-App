from datetime import datetime, timedelta

from apps.api.src.models.worker_profile import WorkerProfile
from apps.api.src.repositories.in_memory_booking_repository import InMemoryBookingRepository
from apps.api.src.repositories.in_memory_worker_profile_repository import (
    InMemoryWorkerProfileRepository,
)
from apps.api.src.services.booking_ops import sweep_no_shows
from packages.domain.src.booking import Booking
from packages.domain.src.booking_state import BookingState


def test_sweep_no_shows_updates_booking_and_reliability():
    booking_repo = InMemoryBookingRepository()
    worker_repo = InMemoryWorkerProfileRepository()
    now = datetime(2030, 1, 1, 12, 0, 0)
    start_time = now - timedelta(hours=1)

    booking = Booking(
        booking_id="booking-1",
        shift_id="shift-1",
        worker_id="worker-1",
        operator_id="operator-1",
        start_time=start_time,
        end_time=start_time + timedelta(hours=4),
        state=BookingState.CONFIRMED,
        created_at=now - timedelta(days=1),
        confirmed_at=now - timedelta(days=1),
    )
    booking_repo.save(booking)

    profile = WorkerProfile(
        worker_id="worker-1",
        display_name="Alex Worker",
        role="server",
        city="Austin",
        experience_years=3,
        reliability_score=1.0,
        badges=[],
        bio=None,
        languages=["en"],
        email=None,
        phone=None,
        address=None,
        emergency_contact=None,
        pay_rate=None,
        notes=None,
        updated_at=now - timedelta(days=1),
    )
    worker_repo.save(profile)

    updated = sweep_no_shows(booking_repo, worker_repo, now)

    assert len(updated) == 1
    assert updated[0].state == BookingState.NO_SHOW

    refreshed = worker_repo.get("worker-1")
    assert refreshed is not None
    assert refreshed.reliability_score == 0.0

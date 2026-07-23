from __future__ import annotations

from dataclasses import replace
from datetime import datetime

from apps.api.src.models.worker_profile import WorkerProfile
from apps.api.src.repositories.booking_repository import BookingRepository
from apps.api.src.repositories.shift_repository import ShiftRepository
from apps.api.src.repositories.worker_profile_repository import WorkerProfileRepository
from packages.domain.src.booking import Booking
from packages.domain.src.booking_state import BookingState
from packages.domain.src.booking_state_machine import TransitionError
from packages.domain.src.reliability import compute_reliability


def refresh_reliability(
    booking_repo: BookingRepository,
    worker_repo: WorkerProfileRepository,
    worker_id: str,
    now: datetime,
) -> WorkerProfile | None:
    profile = worker_repo.get(worker_id)
    if profile is None:
        return None
    score = compute_reliability(booking_repo.list_by_worker(worker_id))
    updated = WorkerProfile(
        worker_id=profile.worker_id,
        display_name=profile.display_name,
        role=profile.role,
        city=profile.city,
        experience_years=profile.experience_years,
        reliability_score=score,
        badges=profile.badges,
        bio=profile.bio,
        languages=profile.languages,
        email=profile.email,
        phone=profile.phone,
        address=profile.address,
        emergency_contact=profile.emergency_contact,
        pay_rate=profile.pay_rate,
        notes=profile.notes,
        updated_at=now,
    )
    return worker_repo.save(updated)


def sweep_no_shows(
    booking_repo: BookingRepository,
    worker_repo: WorkerProfileRepository,
    shift_repo: ShiftRepository,
    now: datetime,
) -> list[Booking]:
    updated: list[Booking] = []

    for booking in booking_repo.list_by_state(BookingState.CONFIRMED):
        try:
            transitioned = booking.transition_to(BookingState.NO_SHOW, now)
        except TransitionError:
            continue
        saved = booking_repo.save(transitioned)
        _decrement_workers_filled(shift_repo, saved.shift_id)
        refresh_reliability(booking_repo, worker_repo, saved.worker_id, now)
        updated.append(saved)

    return updated


def _decrement_workers_filled(shift_repo: ShiftRepository, shift_id: str) -> None:
    shift = shift_repo.get(shift_id)
    if shift is None or shift.workers_filled <= 0:
        return
    shift_repo.save(replace(
        shift,
        workers_filled=shift.workers_filled - 1,
        status="open" if shift.status == "filled" else shift.status,
    ))

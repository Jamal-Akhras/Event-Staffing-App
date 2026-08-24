from __future__ import annotations

from dataclasses import asdict
from datetime import datetime

from fastapi import HTTPException

from apps.api.src.datetime_utils import utc_now
from apps.api.src.models.application import Application
from apps.api.src.models.shift import Shift
from apps.api.src.models.worker_profile import WorkerProfile
from apps.api.src.repositories.worker_profile_repository import WorkerProfileRepository
from apps.api.src.schemas import (
    ApplicationResponse,
    BookingResponse,
    ShiftResponse,
    WorkerProfilePrivateResponse,
)
from packages.domain.src.booking import Booking
from packages.domain.src.booking_state_machine import allowed_next_states

def _now() -> datetime:
    return utc_now()


def _now_or(request_time: datetime | None) -> datetime:
    return request_time or utc_now()


def _get_worker_profile(repo: WorkerProfileRepository, worker_id: str) -> WorkerProfile:
    profile = repo.get(worker_id)
    if profile is None:
        raise HTTPException(status_code=404, detail="Worker profile not found.")
    return profile


def _save_worker_profile(repo: WorkerProfileRepository, profile: WorkerProfile) -> WorkerProfile:
    return repo.save(profile)


def _booking_view(booking: Booking) -> BookingResponse:
    payload = asdict(booking)
    payload["state"] = booking.state.value
    payload["allowed_transitions"] = [
        state.value for state in allowed_next_states(booking.state)
    ]
    return BookingResponse(**payload)


def _shift_view(shift: Shift) -> ShiftResponse:
    payload = asdict(shift)
    return ShiftResponse(**payload)


def _application_view(application: Application) -> ApplicationResponse:
    payload = asdict(application)
    return ApplicationResponse(**payload)


def _worker_public_view(profile: WorkerProfile) -> WorkerProfilePrivateResponse:
    payload = asdict(profile)
    payload["email"] = None
    payload["phone"] = None
    payload["address"] = None
    payload["emergency_contact"] = None
    payload["pay_rate"] = None
    payload["notes"] = None
    return WorkerProfilePrivateResponse(**payload)


def _worker_private_view(profile: WorkerProfile) -> WorkerProfilePrivateResponse:
    payload = asdict(profile)
    return WorkerProfilePrivateResponse(**payload)


from __future__ import annotations

from dataclasses import asdict, replace
from datetime import datetime
from uuid import uuid4

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from apps.api.src.auth import ActorRole, get_actor_role, require_role
from apps.api.src.deps import (
    get_application_repo,
    get_booking_repo,
    get_shift_repo,
    get_worker_profile_repo,
)
from apps.api.src.models.application import Application
from apps.api.src.models.shift import Shift
from apps.api.src.models.worker_profile import WorkerProfile
from apps.api.src.repositories.application_repository import ApplicationRepository
from apps.api.src.repositories.booking_repository import BookingRepository
from apps.api.src.repositories.shift_repository import ShiftRepository
from apps.api.src.repositories.worker_profile_repository import WorkerProfileRepository
from apps.api.src.schemas import (
    ApplicationCreateRequest,
    ApplicationDecisionRequest,
    ApplicationResponse,
    BookingCreateRequest,
    BookingResponse,
    BookingTransitionRequest,
    ErrorResponse,
    ShiftCreateRequest,
    ShiftResponse,
    WorkerProfilePrivateResponse,
    WorkerProfileUpdateRequest,
)
from packages.domain.src.booking import Booking
from packages.domain.src.booking_state import BookingState
from packages.domain.src.booking_state_machine import TransitionError, allowed_next_states


app = FastAPI(title="Event Staffing Platform API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


def _now_or(request_time: datetime | None) -> datetime:
    return request_time or datetime.utcnow()


def _get_booking(repo: BookingRepository, booking_id: str) -> Booking:
    booking = repo.get(booking_id)
    if booking is None:
        raise HTTPException(status_code=404, detail="Booking not found.")
    return booking


def _save_booking(repo: BookingRepository, booking: Booking) -> Booking:
    return repo.save(booking)


def _get_shift(repo: ShiftRepository, shift_id: str) -> Shift:
    shift = repo.get(shift_id)
    if shift is None:
        raise HTTPException(status_code=404, detail="Shift not found.")
    return shift


def _save_shift(repo: ShiftRepository, shift: Shift) -> Shift:
    return repo.save(shift)


def _get_application(repo: ApplicationRepository, application_id: str) -> Application:
    application = repo.get(application_id)
    if application is None:
        raise HTTPException(status_code=404, detail="Application not found.")
    return application


def _save_application(repo: ApplicationRepository, application: Application) -> Application:
    return repo.save(application)


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


def _apply_transition(booking: Booking, target: BookingState, now: datetime) -> Booking:
    try:
        return booking.transition_to(target, now)
    except TransitionError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post(
    "/bookings",
    response_model=BookingResponse,
    responses={400: {"model": ErrorResponse}},
)
def create_booking(
    request: BookingCreateRequest,
    repo: BookingRepository = Depends(get_booking_repo),
    actor: ActorRole = Depends(get_actor_role),
) -> BookingResponse:
    require_role(actor, {ActorRole.OPERATOR})
    booking_id = str(uuid4())
    now = _now_or(request.now)
    booking = Booking(
        booking_id=booking_id,
        shift_id=request.shift_id,
        worker_id=request.worker_id,
        operator_id=request.operator_id,
        start_time=request.start_time,
        end_time=request.end_time,
        created_at=now,
    )
    return _booking_view(_save_booking(repo, booking))


@app.get(
    "/bookings/{booking_id}",
    response_model=BookingResponse,
    responses={404: {"model": ErrorResponse}},
)
def get_booking(
    booking_id: str,
    repo: BookingRepository = Depends(get_booking_repo),
    actor: ActorRole = Depends(get_actor_role),
) -> BookingResponse:
    require_role(actor, {ActorRole.OPERATOR, ActorRole.WORKER})
    return _booking_view(_get_booking(repo, booking_id))


@app.get(
    "/bookings",
    response_model=list[BookingResponse],
)
def list_bookings(
    limit: int = 25,
    worker_id: str | None = None,
    repo: BookingRepository = Depends(get_booking_repo),
    actor: ActorRole = Depends(get_actor_role),
) -> list[BookingResponse]:
    require_role(actor, {ActorRole.OPERATOR, ActorRole.WORKER})
    items = repo.list_recent(limit)
    if worker_id:
        items = [item for item in items if item.worker_id == worker_id]
    return [_booking_view(booking) for booking in items]


@app.post(
    "/shifts",
    response_model=ShiftResponse,
    responses={400: {"model": ErrorResponse}},
)
def create_shift(
    request: ShiftCreateRequest,
    repo: ShiftRepository = Depends(get_shift_repo),
    actor: ActorRole = Depends(get_actor_role),
) -> ShiftResponse:
    require_role(actor, {ActorRole.OPERATOR})
    now = _now_or(request.now)
    shift = Shift(
        shift_id=str(uuid4()),
        operator_id=request.operator_id,
        role=request.role,
        location=request.location,
        start_time=request.start_time,
        end_time=request.end_time,
        pay_rate=request.pay_rate,
        notes=request.notes,
        status="open",
        created_at=now,
    )
    return _shift_view(_save_shift(repo, shift))


@app.get(
    "/shifts",
    response_model=list[ShiftResponse],
)
def list_shifts(
    limit: int = 50,
    role: str | None = None,
    location: str | None = None,
    repo: ShiftRepository = Depends(get_shift_repo),
    actor: ActorRole = Depends(get_actor_role),
) -> list[ShiftResponse]:
    require_role(actor, {ActorRole.OPERATOR, ActorRole.WORKER})
    items = repo.list_recent(limit)
    if role:
        items = [item for item in items if item.role == role]
    if location:
        items = [item for item in items if item.location == location]
    return [_shift_view(item) for item in items]


@app.post(
    "/applications",
    response_model=ApplicationResponse,
    responses={400: {"model": ErrorResponse}, 404: {"model": ErrorResponse}},
)
def create_application(
    request: ApplicationCreateRequest,
    repo: ApplicationRepository = Depends(get_application_repo),
    shift_repo: ShiftRepository = Depends(get_shift_repo),
    actor: ActorRole = Depends(get_actor_role),
) -> ApplicationResponse:
    require_role(actor, {ActorRole.WORKER})
    shift = _get_shift(shift_repo, request.shift_id)
    if shift.status != "open":
        raise HTTPException(status_code=400, detail="Shift is not accepting applications.")
    now = _now_or(request.now)
    application = Application(
        application_id=str(uuid4()),
        shift_id=shift.shift_id,
        worker_id=request.worker_id,
        operator_id=shift.operator_id,
        start_time=shift.start_time,
        end_time=shift.end_time,
        message=request.message,
        booking_id=None,
        status="applied",
        created_at=now,
    )
    return _application_view(_save_application(repo, application))


@app.get(
    "/applications",
    response_model=list[ApplicationResponse],
)
def list_applications(
    limit: int = 50,
    status: str | None = None,
    worker_id: str | None = None,
    shift_id: str | None = None,
    repo: ApplicationRepository = Depends(get_application_repo),
    actor: ActorRole = Depends(get_actor_role),
) -> list[ApplicationResponse]:
    if actor == ActorRole.WORKER and not worker_id:
        raise HTTPException(status_code=400, detail="worker_id is required.")
    require_role(actor, {ActorRole.OPERATOR, ActorRole.WORKER})
    items = repo.list_recent(limit)
    if worker_id:
        items = [item for item in items if item.worker_id == worker_id]
    if shift_id:
        items = [item for item in items if item.shift_id == shift_id]
    if status:
        items = [item for item in items if item.status == status]
    return [_application_view(item) for item in items]


@app.post(
    "/applications/{application_id}/approve",
    response_model=ApplicationResponse,
    responses={400: {"model": ErrorResponse}, 404: {"model": ErrorResponse}},
)
def approve_application(
    application_id: str,
    request: ApplicationDecisionRequest,
    repo: ApplicationRepository = Depends(get_application_repo),
    booking_repo: BookingRepository = Depends(get_booking_repo),
    shift_repo: ShiftRepository = Depends(get_shift_repo),
    actor: ActorRole = Depends(get_actor_role),
) -> ApplicationResponse:
    require_role(actor, {ActorRole.OPERATOR})
    application = _get_application(repo, application_id)
    if application.status != "applied":
        raise HTTPException(status_code=400, detail="Application already decided.")
    now = _now_or(request.now)
    booking = Booking(
        booking_id=str(uuid4()),
        shift_id=application.shift_id,
        worker_id=application.worker_id,
        operator_id=application.operator_id,
        start_time=application.start_time,
        end_time=application.end_time,
        created_at=now,
    )
    booking = booking.transition_to(BookingState.CONFIRMED, now)
    _save_booking(booking_repo, booking)

    shift = _get_shift(shift_repo, application.shift_id)
    shift = replace(shift, status="filled")
    _save_shift(shift_repo, shift)

    application = replace(
        application,
        status="approved",
        decided_at=now,
        booking_id=booking.booking_id,
    )
    return _application_view(_save_application(repo, application))


@app.post(
    "/applications/{application_id}/reject",
    response_model=ApplicationResponse,
    responses={400: {"model": ErrorResponse}, 404: {"model": ErrorResponse}},
)
def reject_application(
    application_id: str,
    request: ApplicationDecisionRequest,
    repo: ApplicationRepository = Depends(get_application_repo),
    actor: ActorRole = Depends(get_actor_role),
) -> ApplicationResponse:
    require_role(actor, {ActorRole.OPERATOR})
    application = _get_application(repo, application_id)
    if application.status != "applied":
        raise HTTPException(status_code=400, detail="Application already decided.")
    now = _now_or(request.now)
    application = replace(application, status="rejected", decided_at=now)
    return _application_view(_save_application(repo, application))


@app.get(
    "/workers/{worker_id}",
    response_model=WorkerProfilePrivateResponse,
    responses={404: {"model": ErrorResponse}},
)
def get_worker_profile(
    worker_id: str,
    repo: WorkerProfileRepository = Depends(get_worker_profile_repo),
    actor: ActorRole = Depends(get_actor_role),
) -> WorkerProfilePrivateResponse:
    require_role(actor, {ActorRole.OPERATOR, ActorRole.WORKER})
    profile = _get_worker_profile(repo, worker_id)
    if actor == ActorRole.WORKER:
        return _worker_private_view(profile)
    return _worker_public_view(profile)


@app.put(
    "/workers/{worker_id}",
    response_model=WorkerProfilePrivateResponse,
    responses={400: {"model": ErrorResponse}},
)
def update_worker_profile(
    worker_id: str,
    request: WorkerProfileUpdateRequest,
    repo: WorkerProfileRepository = Depends(get_worker_profile_repo),
    actor: ActorRole = Depends(get_actor_role),
) -> WorkerProfilePrivateResponse:
    require_role(actor, {ActorRole.WORKER})
    now = _now_or(request.now)
    existing = repo.get(worker_id)
    reliability_score = 0.0 if existing is None else existing.reliability_score
    badges = [] if existing is None else existing.badges
    profile = WorkerProfile(
        worker_id=worker_id,
        display_name=request.display_name,
        role=request.role,
        city=request.city,
        experience_years=request.experience_years,
        reliability_score=reliability_score,
        badges=badges,
        bio=request.bio,
        languages=request.languages,
        email=request.email,
        phone=request.phone,
        address=request.address,
        emergency_contact=request.emergency_contact,
        pay_rate=request.pay_rate,
        notes=request.notes,
        updated_at=now,
    )
    return _worker_private_view(_save_worker_profile(repo, profile))


@app.post(
    "/bookings/{booking_id}/confirm",
    response_model=BookingResponse,
    responses={400: {"model": ErrorResponse}, 404: {"model": ErrorResponse}},
)
def confirm_booking(
    booking_id: str,
    request: BookingTransitionRequest,
    repo: BookingRepository = Depends(get_booking_repo),
    actor: ActorRole = Depends(get_actor_role),
) -> BookingResponse:
    require_role(actor, {ActorRole.OPERATOR})
    booking = _get_booking(repo, booking_id)
    booking = _apply_transition(booking, BookingState.CONFIRMED, _now_or(request.now))
    return _booking_view(_save_booking(repo, booking))


@app.post(
    "/bookings/{booking_id}/check-in",
    response_model=BookingResponse,
    responses={400: {"model": ErrorResponse}, 404: {"model": ErrorResponse}},
)
def check_in_booking(
    booking_id: str,
    request: BookingTransitionRequest,
    repo: BookingRepository = Depends(get_booking_repo),
    actor: ActorRole = Depends(get_actor_role),
) -> BookingResponse:
    require_role(actor, {ActorRole.WORKER})
    booking = _get_booking(repo, booking_id)
    booking = _apply_transition(booking, BookingState.CHECKED_IN, _now_or(request.now))
    return _booking_view(_save_booking(repo, booking))


@app.post(
    "/bookings/{booking_id}/check-out",
    response_model=BookingResponse,
    responses={400: {"model": ErrorResponse}, 404: {"model": ErrorResponse}},
)
def check_out_booking(
    booking_id: str,
    request: BookingTransitionRequest,
    repo: BookingRepository = Depends(get_booking_repo),
    actor: ActorRole = Depends(get_actor_role),
) -> BookingResponse:
    require_role(actor, {ActorRole.WORKER})
    booking = _get_booking(repo, booking_id)
    booking = _apply_transition(booking, BookingState.CHECKED_OUT, _now_or(request.now))
    return _booking_view(_save_booking(repo, booking))


@app.post(
    "/bookings/{booking_id}/approve",
    response_model=BookingResponse,
    responses={400: {"model": ErrorResponse}, 404: {"model": ErrorResponse}},
)
def approve_booking(
    booking_id: str,
    request: BookingTransitionRequest,
    repo: BookingRepository = Depends(get_booking_repo),
    actor: ActorRole = Depends(get_actor_role),
) -> BookingResponse:
    require_role(actor, {ActorRole.OPERATOR})
    booking = _get_booking(repo, booking_id)
    booking = _apply_transition(booking, BookingState.APPROVED, _now_or(request.now))
    return _booking_view(_save_booking(repo, booking))


@app.post(
    "/bookings/{booking_id}/pay",
    response_model=BookingResponse,
    responses={400: {"model": ErrorResponse}, 404: {"model": ErrorResponse}},
)
def pay_booking(
    booking_id: str,
    request: BookingTransitionRequest,
    repo: BookingRepository = Depends(get_booking_repo),
    actor: ActorRole = Depends(get_actor_role),
) -> BookingResponse:
    require_role(actor, {ActorRole.OPERATOR, ActorRole.SYSTEM})
    booking = _get_booking(repo, booking_id)
    booking = _apply_transition(booking, BookingState.PAID, _now_or(request.now))
    return _booking_view(_save_booking(repo, booking))


@app.post(
    "/bookings/{booking_id}/no-show",
    response_model=BookingResponse,
    responses={400: {"model": ErrorResponse}, 404: {"model": ErrorResponse}},
)
def no_show_booking(
    booking_id: str,
    request: BookingTransitionRequest,
    repo: BookingRepository = Depends(get_booking_repo),
    actor: ActorRole = Depends(get_actor_role),
) -> BookingResponse:
    require_role(actor, {ActorRole.OPERATOR, ActorRole.SYSTEM})
    booking = _get_booking(repo, booking_id)
    booking = _apply_transition(booking, BookingState.NO_SHOW, _now_or(request.now))
    return _booking_view(_save_booking(repo, booking))


@app.post(
    "/bookings/{booking_id}/cancel/worker",
    response_model=BookingResponse,
    responses={400: {"model": ErrorResponse}, 404: {"model": ErrorResponse}},
)
def cancel_by_worker(
    booking_id: str,
    request: BookingTransitionRequest,
    repo: BookingRepository = Depends(get_booking_repo),
    actor: ActorRole = Depends(get_actor_role),
) -> BookingResponse:
    require_role(actor, {ActorRole.WORKER})
    booking = _get_booking(repo, booking_id)
    booking = _apply_transition(booking, BookingState.CANCELLED_BY_WORKER, _now_or(request.now))
    return _booking_view(_save_booking(repo, booking))


@app.post(
    "/bookings/{booking_id}/cancel/operator",
    response_model=BookingResponse,
    responses={400: {"model": ErrorResponse}, 404: {"model": ErrorResponse}},
)
def cancel_by_operator(
    booking_id: str,
    request: BookingTransitionRequest,
    repo: BookingRepository = Depends(get_booking_repo),
    actor: ActorRole = Depends(get_actor_role),
) -> BookingResponse:
    require_role(actor, {ActorRole.OPERATOR})
    booking = _get_booking(repo, booking_id)
    booking = _apply_transition(booking, BookingState.CANCELLED_BY_OPERATOR, _now_or(request.now))
    return _booking_view(_save_booking(repo, booking))

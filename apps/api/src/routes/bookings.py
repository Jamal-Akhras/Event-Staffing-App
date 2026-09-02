from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, Request

from apps.api.src.auth import ActorContext, ActorRole, get_actor_context, require_role
from apps.api.src.deps import (
    get_booking_lifecycle_service,
    get_booking_transition_repo,
    get_charge_recorder,
    get_event_recorder,
    get_relationship_service,
)
from apps.api.src.rate_limit import actor_or_ip, limiter
from apps.api.src.routes.actor_scope import list_scope
from apps.api.src.routes.approval_effects import record_approval_effects
from apps.api.src.routes.presenters import BookingPresenter, get_booking_presenter
from apps.api.src.routes.service_errors import raise_service_error
from apps.api.src.schemas import (
    BookingResponse,
    BookingTransitionRequest,
    ErrorResponse,
)
from apps.api.src.repositories.booking_transition_repository import BookingTransitionRepository
from apps.api.src.schemas_recovery import BookingTransitionView, CancellationRequest, PaymentRecordRequest
from apps.api.src.services.booking_lifecycle_service import BookingLifecycleService
from apps.api.src.services.charge_recorder import ChargeRecorder
from apps.api.src.services.relationship_service import RelationshipService
from apps.api.src.services.errors import ServiceError
from apps.api.src.services.event_recorder import EventRecorder
from packages.domain.src.booking import Booking
from packages.domain.src.booking_state import BookingState

router = APIRouter(tags=["bookings"])


@router.get("/bookings/{booking_id}", response_model=BookingResponse, responses={404: {"model": ErrorResponse}})
def get_booking(
    booking_id: str,
    service: BookingLifecycleService = Depends(get_booking_lifecycle_service),
    actor: ActorContext = Depends(get_actor_context),
    present: BookingPresenter = Depends(get_booking_presenter),
) -> BookingResponse:
    try:
        booking = service.get_booking(booking_id)
        _require_booking_access(actor, booking, service)
        return present.one(booking)
    except ServiceError as exc:
        raise_service_error(exc)


@router.get("/bookings/{booking_id}/transitions", response_model=list[BookingTransitionView], responses={404: {"model": ErrorResponse}})
def booking_transitions(
    booking_id: str,
    service: BookingLifecycleService = Depends(get_booking_lifecycle_service),
    transitions: BookingTransitionRepository = Depends(get_booking_transition_repo),
    actor: ActorContext = Depends(get_actor_context),
) -> list[BookingTransitionView]:
    try:
        _require_booking_access(actor, service.get_booking(booking_id), service)
    except ServiceError as exc:
        raise_service_error(exc)
    return [
        BookingTransitionView(**{field: getattr(item, field) for field in BookingTransitionView.model_fields})
        for item in transitions.list_for_booking(booking_id)
    ]


@router.get("/bookings", response_model=list[BookingResponse])
def list_bookings(
    limit: int = Query(default=25, ge=1, le=100),
    worker_id: str | None = None,
    service: BookingLifecycleService = Depends(get_booking_lifecycle_service),
    actor: ActorContext = Depends(get_actor_context),
    present: BookingPresenter = Depends(get_booking_presenter),
) -> list[BookingResponse]:
    require_role(actor.role, {ActorRole.OPERATOR, ActorRole.WORKER})
    worker_id, operator_id, account_id = list_scope(actor, worker_id, "bookings")
    items = service.list_bookings(limit, worker_id, operator_id, account_id)
    return present.many(items)


@router.post("/bookings/{booking_id}/confirm", response_model=BookingResponse, responses={400: {"model": ErrorResponse}, 404: {"model": ErrorResponse}})
def confirm_booking(
    booking_id: str,
    request: BookingTransitionRequest,
    service: BookingLifecycleService = Depends(get_booking_lifecycle_service),
    actor: ActorContext = Depends(get_actor_context),
    present: BookingPresenter = Depends(get_booking_presenter),
    recorder: EventRecorder = Depends(get_event_recorder),
) -> BookingResponse:
    require_role(actor.role, {ActorRole.OPERATOR})
    return _transition(service, booking_id, BookingState.CONFIRMED, request, actor, recorder=recorder, present=present)


@router.post("/bookings/{booking_id}/check-in", response_model=BookingResponse, responses={400: {"model": ErrorResponse}, 404: {"model": ErrorResponse}})
@limiter.limit("5/minute", key_func=actor_or_ip)
def check_in_booking(
    booking_id: str,
    request: Request,
    payload: BookingTransitionRequest,
    service: BookingLifecycleService = Depends(get_booking_lifecycle_service),
    actor: ActorContext = Depends(get_actor_context),
    present: BookingPresenter = Depends(get_booking_presenter),
    recorder: EventRecorder = Depends(get_event_recorder),
) -> BookingResponse:
    require_role(actor.role, {ActorRole.WORKER})
    return _transition(service, booking_id, BookingState.CHECKED_IN, payload, actor, recorder=recorder, present=present)


@router.post("/bookings/{booking_id}/check-out", response_model=BookingResponse, responses={400: {"model": ErrorResponse}, 404: {"model": ErrorResponse}})
def check_out_booking(
    booking_id: str,
    request: BookingTransitionRequest,
    service: BookingLifecycleService = Depends(get_booking_lifecycle_service),
    actor: ActorContext = Depends(get_actor_context),
    present: BookingPresenter = Depends(get_booking_presenter),
    recorder: EventRecorder = Depends(get_event_recorder),
) -> BookingResponse:
    require_role(actor.role, {ActorRole.WORKER})
    return _transition(service, booking_id, BookingState.CHECKED_OUT, request, actor, True, recorder=recorder, present=present)


@router.post("/bookings/{booking_id}/approve", response_model=BookingResponse, responses={400: {"model": ErrorResponse}, 404: {"model": ErrorResponse}})
@limiter.limit("5/minute", key_func=actor_or_ip)
def approve_booking(
    booking_id: str,
    request: Request,
    payload: BookingTransitionRequest,
    service: BookingLifecycleService = Depends(get_booking_lifecycle_service),
    actor: ActorContext = Depends(get_actor_context),
    present: BookingPresenter = Depends(get_booking_presenter),
    recorder: EventRecorder = Depends(get_event_recorder),
    charges: ChargeRecorder = Depends(get_charge_recorder),
    relationships: RelationshipService = Depends(get_relationship_service),
) -> BookingResponse:
    require_role(actor.role, {ActorRole.OPERATOR})
    return _transition(
        service,
        booking_id,
        BookingState.APPROVED,
        payload,
        actor,
        True,
        recorder=recorder,
        present=present,
        charges=charges,
        relationships=relationships,
    )


@router.post("/bookings/{booking_id}/pay", response_model=BookingResponse, responses={400: {"model": ErrorResponse}, 404: {"model": ErrorResponse}})
@router.post("/bookings/{booking_id}/record-payment", response_model=BookingResponse, responses={400: {"model": ErrorResponse}, 404: {"model": ErrorResponse}})
@limiter.limit("10/hour", key_func=actor_or_ip)
def pay_booking(
    booking_id: str,
    request: Request,
    payload: PaymentRecordRequest,
    service: BookingLifecycleService = Depends(get_booking_lifecycle_service),
    actor: ActorContext = Depends(get_actor_context),
    present: BookingPresenter = Depends(get_booking_presenter),
    recorder: EventRecorder = Depends(get_event_recorder),
) -> BookingResponse:
    require_role(actor.role, {ActorRole.OPERATOR})
    return _transition(service, booking_id, BookingState.PAID, payload, actor, True, recorder=recorder, present=present)


@router.post("/bookings/{booking_id}/no-show", response_model=BookingResponse, responses={400: {"model": ErrorResponse}, 404: {"model": ErrorResponse}})
def no_show_booking(
    booking_id: str,
    request: BookingTransitionRequest,
    service: BookingLifecycleService = Depends(get_booking_lifecycle_service),
    actor: ActorContext = Depends(get_actor_context),
    present: BookingPresenter = Depends(get_booking_presenter),
    recorder: EventRecorder = Depends(get_event_recorder),
) -> BookingResponse:
    require_role(actor.role, {ActorRole.OPERATOR, ActorRole.SYSTEM})
    return _transition(service, booking_id, BookingState.NO_SHOW, request, actor, True, recorder=recorder, present=present)


@router.post("/bookings/{booking_id}/cancel/worker", response_model=BookingResponse, responses={400: {"model": ErrorResponse}, 404: {"model": ErrorResponse}})
def cancel_by_worker(
    booking_id: str,
    request: CancellationRequest,
    service: BookingLifecycleService = Depends(get_booking_lifecycle_service),
    actor: ActorContext = Depends(get_actor_context),
    present: BookingPresenter = Depends(get_booking_presenter),
    recorder: EventRecorder = Depends(get_event_recorder),
) -> BookingResponse:
    require_role(actor.role, {ActorRole.WORKER})
    return _transition(service, booking_id, BookingState.CANCELLED_BY_WORKER, request, actor, True, recorder=recorder, present=present)


@router.post("/bookings/{booking_id}/cancel/operator", response_model=BookingResponse, responses={400: {"model": ErrorResponse}, 404: {"model": ErrorResponse}})
def cancel_by_operator(
    booking_id: str,
    request: CancellationRequest,
    service: BookingLifecycleService = Depends(get_booking_lifecycle_service),
    actor: ActorContext = Depends(get_actor_context),
    present: BookingPresenter = Depends(get_booking_presenter),
    recorder: EventRecorder = Depends(get_event_recorder),
) -> BookingResponse:
    require_role(actor.role, {ActorRole.OPERATOR})
    return _transition(service, booking_id, BookingState.CANCELLED_BY_OPERATOR, request, actor, recorder=recorder, present=present)


@router.post("/system/no-show-sweep", response_model=list[BookingResponse], responses={400: {"model": ErrorResponse}})
def sweep_no_shows(
    request: BookingTransitionRequest,
    service: BookingLifecycleService = Depends(get_booking_lifecycle_service),
    actor: ActorContext = Depends(get_actor_context),
    present: BookingPresenter = Depends(get_booking_presenter),
) -> list[BookingResponse]:
    require_role(actor.role, {ActorRole.SYSTEM})
    updated = service.sweep_no_shows(request)
    return present.many(updated)


def _transition(
    service: BookingLifecycleService,
    booking_id: str,
    target: BookingState,
    request: BookingTransitionRequest | CancellationRequest | PaymentRecordRequest,
    actor: ActorContext,
    refresh_worker_reliability: bool = False,
    *,
    recorder: EventRecorder,
    present: BookingPresenter,
    charges: ChargeRecorder | None = None,
    relationships: RelationshipService | None = None,
) -> BookingResponse:
    try:
        _require_booking_access(actor, service.get_booking(booking_id), service)
        booking = service.transition(
            booking_id,
            target,
            request,
            actor.user_id,
            refresh_worker_reliability,
            actor_role=actor.role.value,
        )
        recorder.record(
            f"booking.{target.value}",
            "lifecycle",
            actor=actor,
            subject_type="booking",
            subject_id=booking.booking_id,
            worker_id=booking.worker_id,
            context={"shift_id": booking.shift_id, "operator_id": booking.operator_id},
        )
        if charges is not None:
            record_approval_effects(booking, actor, recorder, charges, relationships)
        return present.one(booking)
    except ServiceError as exc:
        raise_service_error(exc)


def _require_booking_access(
    actor: ActorContext,
    booking: Booking,
    service: BookingLifecycleService,
) -> None:
    if actor.role == ActorRole.SYSTEM:
        return
    require_role(actor.role, {ActorRole.OPERATOR, ActorRole.WORKER})
    if (
        actor.role == ActorRole.OPERATOR
        and booking.operator_id != actor.user_id
        and not service.booking_belongs_to_venue(booking, actor.account_id)
    ):
        raise HTTPException(status_code=403, detail="Operator can only access their own bookings.")
    if actor.role == ActorRole.WORKER and booking.worker_id != actor.effective_worker_id:
        raise HTTPException(status_code=403, detail="Worker can only access their own bookings.")

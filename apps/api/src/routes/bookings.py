from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, Request

from apps.api.src.auth import ActorContext, ActorRole, get_actor_context, require_role
from apps.api.src.deps import get_booking_lifecycle_service
from apps.api.src.helpers import (
    _booking_view,
)
from apps.api.src.rate_limit import actor_or_ip, limiter
from apps.api.src.routes.service_errors import raise_service_error
from apps.api.src.schemas import (
    BookingResponse,
    BookingTransitionRequest,
    ErrorResponse,
)
from apps.api.src.schemas_recovery import CancellationRequest, PaymentRecordRequest
from apps.api.src.services.booking_lifecycle_service import BookingLifecycleService
from apps.api.src.services.errors import ServiceError
from packages.domain.src.booking import Booking
from packages.domain.src.booking_state import BookingState

router = APIRouter(tags=["bookings"])


@router.get("/bookings/{booking_id}", response_model=BookingResponse, responses={404: {"model": ErrorResponse}})
def get_booking(
    booking_id: str,
    service: BookingLifecycleService = Depends(get_booking_lifecycle_service),
    actor: ActorContext = Depends(get_actor_context),
) -> BookingResponse:
    try:
        booking = service.get_booking(booking_id)
        _require_booking_access(actor, booking, service)
        return _booking_view(booking)
    except ServiceError as exc:
        raise_service_error(exc)


@router.get("/bookings", response_model=list[BookingResponse])
def list_bookings(
    limit: int = Query(default=25, ge=1, le=100),
    worker_id: str | None = None,
    service: BookingLifecycleService = Depends(get_booking_lifecycle_service),
    actor: ActorContext = Depends(get_actor_context),
) -> list[BookingResponse]:
    require_role(actor.role, {ActorRole.OPERATOR, ActorRole.WORKER})
    if actor.role == ActorRole.WORKER:
        effective_worker_id = actor.worker_profile_id or actor.user_id
        if worker_id is not None and worker_id != effective_worker_id:
            raise HTTPException(status_code=403, detail="Worker can only access their own bookings.")
        worker_id = effective_worker_id
    account_id = actor.account_id if actor.role == ActorRole.OPERATOR else None
    operator_id = actor.user_id if actor.role == ActorRole.OPERATOR and account_id is None else None
    items = service.list_bookings(limit, worker_id, operator_id, account_id)
    return [_booking_view(booking) for booking in items]


@router.post("/bookings/{booking_id}/confirm", response_model=BookingResponse, responses={400: {"model": ErrorResponse}, 404: {"model": ErrorResponse}})
def confirm_booking(
    booking_id: str,
    request: BookingTransitionRequest,
    service: BookingLifecycleService = Depends(get_booking_lifecycle_service),
    actor: ActorContext = Depends(get_actor_context),
) -> BookingResponse:
    require_role(actor.role, {ActorRole.OPERATOR})
    return _transition(service, booking_id, BookingState.CONFIRMED, request, actor)


@router.post("/bookings/{booking_id}/check-in", response_model=BookingResponse, responses={400: {"model": ErrorResponse}, 404: {"model": ErrorResponse}})
def check_in_booking(
    booking_id: str,
    request: BookingTransitionRequest,
    service: BookingLifecycleService = Depends(get_booking_lifecycle_service),
    actor: ActorContext = Depends(get_actor_context),
) -> BookingResponse:
    require_role(actor.role, {ActorRole.WORKER})
    return _transition(service, booking_id, BookingState.CHECKED_IN, request, actor)


@router.post("/bookings/{booking_id}/check-out", response_model=BookingResponse, responses={400: {"model": ErrorResponse}, 404: {"model": ErrorResponse}})
def check_out_booking(
    booking_id: str,
    request: BookingTransitionRequest,
    service: BookingLifecycleService = Depends(get_booking_lifecycle_service),
    actor: ActorContext = Depends(get_actor_context),
) -> BookingResponse:
    require_role(actor.role, {ActorRole.WORKER})
    return _transition(service, booking_id, BookingState.CHECKED_OUT, request, actor, True)


@router.post("/bookings/{booking_id}/approve", response_model=BookingResponse, responses={400: {"model": ErrorResponse}, 404: {"model": ErrorResponse}})
def approve_booking(
    booking_id: str,
    request: BookingTransitionRequest,
    service: BookingLifecycleService = Depends(get_booking_lifecycle_service),
    actor: ActorContext = Depends(get_actor_context),
) -> BookingResponse:
    require_role(actor.role, {ActorRole.OPERATOR})
    return _transition(service, booking_id, BookingState.APPROVED, request, actor, True)


@router.post("/bookings/{booking_id}/pay", response_model=BookingResponse, responses={400: {"model": ErrorResponse}, 404: {"model": ErrorResponse}})
@router.post("/bookings/{booking_id}/record-payment", response_model=BookingResponse, responses={400: {"model": ErrorResponse}, 404: {"model": ErrorResponse}})
@limiter.limit("10/hour", key_func=actor_or_ip)
def pay_booking(
    booking_id: str,
    request: Request,
    payload: PaymentRecordRequest,
    service: BookingLifecycleService = Depends(get_booking_lifecycle_service),
    actor: ActorContext = Depends(get_actor_context),
) -> BookingResponse:
    require_role(actor.role, {ActorRole.OPERATOR})
    return _transition(service, booking_id, BookingState.PAID, payload, actor, True)


@router.post("/bookings/{booking_id}/no-show", response_model=BookingResponse, responses={400: {"model": ErrorResponse}, 404: {"model": ErrorResponse}})
def no_show_booking(
    booking_id: str,
    request: BookingTransitionRequest,
    service: BookingLifecycleService = Depends(get_booking_lifecycle_service),
    actor: ActorContext = Depends(get_actor_context),
) -> BookingResponse:
    require_role(actor.role, {ActorRole.OPERATOR, ActorRole.SYSTEM})
    return _transition(service, booking_id, BookingState.NO_SHOW, request, actor, True)


@router.post("/bookings/{booking_id}/cancel/worker", response_model=BookingResponse, responses={400: {"model": ErrorResponse}, 404: {"model": ErrorResponse}})
def cancel_by_worker(
    booking_id: str,
    request: CancellationRequest,
    service: BookingLifecycleService = Depends(get_booking_lifecycle_service),
    actor: ActorContext = Depends(get_actor_context),
) -> BookingResponse:
    require_role(actor.role, {ActorRole.WORKER})
    return _transition(service, booking_id, BookingState.CANCELLED_BY_WORKER, request, actor, True)


@router.post("/bookings/{booking_id}/cancel/operator", response_model=BookingResponse, responses={400: {"model": ErrorResponse}, 404: {"model": ErrorResponse}})
def cancel_by_operator(
    booking_id: str,
    request: CancellationRequest,
    service: BookingLifecycleService = Depends(get_booking_lifecycle_service),
    actor: ActorContext = Depends(get_actor_context),
) -> BookingResponse:
    require_role(actor.role, {ActorRole.OPERATOR})
    return _transition(service, booking_id, BookingState.CANCELLED_BY_OPERATOR, request, actor)


@router.post("/system/no-show-sweep", response_model=list[BookingResponse], responses={400: {"model": ErrorResponse}})
def sweep_no_shows(
    request: BookingTransitionRequest,
    service: BookingLifecycleService = Depends(get_booking_lifecycle_service),
    actor: ActorContext = Depends(get_actor_context),
) -> list[BookingResponse]:
    require_role(actor.role, {ActorRole.SYSTEM})
    updated = service.sweep_no_shows(request)
    return [_booking_view(item) for item in updated]


def _transition(
    service: BookingLifecycleService,
    booking_id: str,
    target: BookingState,
    request: BookingTransitionRequest | CancellationRequest | PaymentRecordRequest,
    actor: ActorContext,
    refresh_worker_reliability: bool = False,
) -> BookingResponse:
    try:
        _require_booking_access(actor, service.get_booking(booking_id), service)
        cancellation_reason = request.reason if isinstance(request, CancellationRequest) else None
        payment = request if isinstance(request, PaymentRecordRequest) else None
        booking = service.transition(
            booking_id,
            target,
            request,
            refresh_worker_reliability,
            cancellation_reason,
            actor.user_id if cancellation_reason else None,
            payment.method if payment else None,
            payment.reference if payment else None,
            actor.user_id if payment else None,
        )
        return _booking_view(booking)
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
    effective_worker_id = actor.worker_profile_id or actor.user_id
    if actor.role == ActorRole.WORKER and booking.worker_id != effective_worker_id:
        raise HTTPException(status_code=403, detail="Worker can only access their own bookings.")

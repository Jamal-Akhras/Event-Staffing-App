from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response

from apps.api.src.auth import (
    ActorContext,
    ActorRole,
    get_actor_context,
    require_role,
    require_verified_actor,
    require_worker_owner,
)
from uuid import uuid4

from apps.api.src.deps import get_application_service, get_booking_transition_repo, get_event_recorder, get_idempotency_service
from apps.api.src.models.application import Application
from apps.api.src.rate_limit import actor_or_ip, limiter
from apps.api.src.routes.actor_scope import list_scope
from apps.api.src.routes.presenters import ApplicationPresenter, get_application_presenter
from apps.api.src.routes.idempotency_support import IdempotencyKeyHeader, replayed
from apps.api.src.routes.service_errors import raise_service_error
from apps.api.src.schemas import (
    ApplicationCreateRequest,
    ApplicationDecisionRequest,
    ApplicationMessageHistoryResponse,
    ApplicationMessageUpdateRequest,
    ApplicationResponse,
    ErrorResponse,
)
from apps.api.src.schemas_recovery import CancellationRequest
from apps.api.src.services.application_service import ApplicationService
from apps.api.src.services.errors import ServiceError
from apps.api.src.datetime_utils import utc_now
from apps.api.src.models.booking_transition import BookingTransition
from apps.api.src.repositories.booking_transition_repository import BookingTransitionRepository
from apps.api.src.services.event_recorder import EventRecorder
from apps.api.src.services.idempotency import IdempotencyConflict, IdempotencyService

router = APIRouter(tags=["applications"])


@router.post("/applications", response_model=ApplicationResponse, responses={400: {"model": ErrorResponse}, 404: {"model": ErrorResponse}})
@limiter.limit("10/minute", key_func=actor_or_ip)
def create_application(
    request: Request,
    payload: ApplicationCreateRequest,
    response: Response,
    idempotency_key: IdempotencyKeyHeader = None,
    idempotency: IdempotencyService = Depends(get_idempotency_service),
    service: ApplicationService = Depends(get_application_service),
    actor: ActorContext = Depends(get_actor_context),
    present: ApplicationPresenter = Depends(get_application_presenter),
    recorder: EventRecorder = Depends(get_event_recorder),
) -> ApplicationResponse:
    require_verified_actor(actor, "applying for shifts")
    require_worker_owner(actor, payload.worker_id)
    try:
        started = idempotency.start(actor.user_id, "application.create", idempotency_key, payload.model_dump(mode="json"))
        if started.cached_response is not None:
            return replayed(response, ApplicationResponse, started.cached_response)
        created = service.create_application(payload)
        recorder.record(
            "application.created",
            "lifecycle",
            actor=actor,
            subject_type="application",
            subject_id=created.application_id,
            worker_id=created.worker_id,
            context={"shift_id": created.shift_id},
        )
        result = present.one(created)
        idempotency.finish(started.record_id, result.model_dump(mode="json"))
        return result
    except IdempotencyConflict as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    except ServiceError as exc:
        raise_service_error(exc)


@router.get("/applications", response_model=list[ApplicationResponse])
def list_applications(
    limit: int = Query(default=50, ge=1, le=100),
    status: str | None = None,
    worker_id: str | None = None,
    shift_id: str | None = None,
    service: ApplicationService = Depends(get_application_service),
    actor: ActorContext = Depends(get_actor_context),
    present: ApplicationPresenter = Depends(get_application_presenter),
) -> list[ApplicationResponse]:
    require_role(actor.role, {ActorRole.OPERATOR, ActorRole.WORKER})
    worker_id, operator_id, account_id = list_scope(actor, worker_id, "applications")
    items = service.list_applications(limit, status, worker_id, operator_id, account_id, shift_id)
    return present.many(items)


@router.post("/applications/{application_id}/approve", response_model=ApplicationResponse, responses={400: {"model": ErrorResponse}, 404: {"model": ErrorResponse}})
def approve_application(
    application_id: str,
    request: ApplicationDecisionRequest,
    service: ApplicationService = Depends(get_application_service),
    actor: ActorContext = Depends(get_actor_context),
    present: ApplicationPresenter = Depends(get_application_presenter),
    recorder: EventRecorder = Depends(get_event_recorder),
    transitions: BookingTransitionRepository = Depends(get_booking_transition_repo),
) -> ApplicationResponse:
    require_role(actor.role, {ActorRole.OPERATOR})
    try:
        _require_application_access(actor, service.get_application(application_id), service)
        application = service.approve_application(application_id, request)
        if application.booking_id:
            transitions.append(
                BookingTransition(
                    transition_id=str(uuid4()),
                    booking_id=application.booking_id,
                    from_state=None,
                    to_state="confirmed",
                    occurred_at=request.now or utc_now(),
                    actor_user_id=actor.user_id,
                    actor_role=actor.role.value,
                    context={"shift_id": application.shift_id, "worker_id": application.worker_id},
                )
            )
        recorder.record(
            "application.approved",
            "lifecycle",
            actor=actor,
            subject_type="application",
            subject_id=application.application_id,
            worker_id=application.worker_id,
            context={"shift_id": application.shift_id, "booking_id": application.booking_id},
        )
        return present.one(application)
    except ServiceError as exc:
        raise_service_error(exc)


@router.post("/applications/{application_id}/reject", response_model=ApplicationResponse, responses={400: {"model": ErrorResponse}, 404: {"model": ErrorResponse}})
def reject_application(
    application_id: str,
    request: ApplicationDecisionRequest,
    service: ApplicationService = Depends(get_application_service),
    actor: ActorContext = Depends(get_actor_context),
    present: ApplicationPresenter = Depends(get_application_presenter),
    recorder: EventRecorder = Depends(get_event_recorder),
) -> ApplicationResponse:
    require_role(actor.role, {ActorRole.OPERATOR})
    try:
        _require_application_access(actor, service.get_application(application_id), service)
        application = service.reject_application(application_id, request)
        recorder.record(
            "application.rejected",
            "lifecycle",
            actor=actor,
            subject_type="application",
            subject_id=application.application_id,
            worker_id=application.worker_id,
            context={"shift_id": application.shift_id, "booking_id": application.booking_id},
        )
        return present.one(application)
    except ServiceError as exc:
        raise_service_error(exc)


@router.post("/applications/{application_id}/withdraw", response_model=ApplicationResponse, responses={400: {"model": ErrorResponse}, 404: {"model": ErrorResponse}})
def withdraw_application(
    application_id: str,
    request: CancellationRequest,
    service: ApplicationService = Depends(get_application_service),
    actor: ActorContext = Depends(get_actor_context),
    present: ApplicationPresenter = Depends(get_application_presenter),
    recorder: EventRecorder = Depends(get_event_recorder),
) -> ApplicationResponse:
    require_role(actor.role, {ActorRole.WORKER})
    try:
        application = service.get_application(application_id)
        _require_application_access(actor, application, service)
        withdrawn = service.withdraw(application_id, request)
        recorder.record(
            "application.withdrawn",
            "lifecycle",
            actor=actor,
            subject_type="application",
            subject_id=withdrawn.application_id,
            worker_id=withdrawn.worker_id,
            context={"shift_id": withdrawn.shift_id},
        )
        return present.one(withdrawn)
    except ServiceError as exc:
        raise_service_error(exc)


@router.put("/applications/{application_id}/message", response_model=ApplicationResponse, responses={400: {"model": ErrorResponse}, 404: {"model": ErrorResponse}})
def update_application_message(
    application_id: str,
    request: ApplicationMessageUpdateRequest,
    service: ApplicationService = Depends(get_application_service),
    actor: ActorContext = Depends(get_actor_context),
    present: ApplicationPresenter = Depends(get_application_presenter),
) -> ApplicationResponse:
    try:
        _require_application_access(actor, service.get_application(application_id), service)
        return present.one(service.update_message(application_id, request))
    except ServiceError as exc:
        raise_service_error(exc)


@router.get("/applications/{application_id}/message-history", response_model=list[ApplicationMessageHistoryResponse], responses={404: {"model": ErrorResponse}})
def get_application_message_history(
    application_id: str,
    service: ApplicationService = Depends(get_application_service),
    actor: ActorContext = Depends(get_actor_context),
    present: ApplicationPresenter = Depends(get_application_presenter),
) -> list[ApplicationMessageHistoryResponse]:
    try:
        _require_application_access(actor, service.get_application(application_id), service)
        records = service.list_message_history(application_id)
        return [
            ApplicationMessageHistoryResponse(
                history_id=record.history_id,
                application_id=record.application_id,
                message=record.message,
                edited_at=record.edited_at,
            )
            for record in records
        ]
    except ServiceError as exc:
        raise_service_error(exc)


def _require_application_access(
    actor: ActorContext,
    application: Application,
    service: ApplicationService,
) -> None:
    require_role(actor.role, {ActorRole.OPERATOR, ActorRole.WORKER})
    if actor.role == ActorRole.WORKER and application.worker_id != actor.effective_worker_id:
        raise HTTPException(status_code=403, detail="Worker can only access their own applications.")
    if (
        actor.role == ActorRole.OPERATOR
        and application.operator_id != actor.user_id
        and not service.application_belongs_to_venue(application, actor.account_id)
    ):
        raise HTTPException(status_code=403, detail="Operator can only access their own applications.")

from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException

from apps.api.src.auth import (
    ActorContext,
    ActorRole,
    get_actor_context,
    require_role,
    require_worker_owner,
)
from apps.api.src.deps import get_application_service, get_notification_repo
from apps.api.src.helpers import (
    _application_view,
)
from apps.api.src.models.application import Application
from apps.api.src.models.notification import Notification
from apps.api.src.repositories.notification_repository import NotificationRepository
from apps.api.src.routes.service_errors import raise_service_error
from apps.api.src.schemas import (
    ApplicationCreateRequest,
    ApplicationDecisionRequest,
    ApplicationMessageHistoryResponse,
    ApplicationMessageUpdateRequest,
    ApplicationResponse,
    ErrorResponse,
)
from apps.api.src.services.application_service import ApplicationService
from apps.api.src.services.errors import ServiceError

router = APIRouter(tags=["applications"])


def _notify_decision(repo: NotificationRepository, application: Application, decision: str) -> None:
    date_str = application.start_time.strftime("%a %d %b")
    title = "Application approved" if decision == "approved" else "Application not selected"
    body = f"Your application for {date_str} has been {decision}."
    try:
        repo.save(Notification(
            notification_id=str(uuid4()),
            worker_id=application.worker_id,
            type=decision,
            title=title,
            body=body,
            shift_id=application.shift_id,
            created_at=datetime.utcnow(),
        ))
    except Exception:
        pass


@router.post("/applications", response_model=ApplicationResponse, responses={400: {"model": ErrorResponse}, 404: {"model": ErrorResponse}})
def create_application(
    request: ApplicationCreateRequest,
    service: ApplicationService = Depends(get_application_service),
    actor: ActorContext = Depends(get_actor_context),
) -> ApplicationResponse:
    require_worker_owner(actor, request.worker_id)
    try:
        return _application_view(service.create_application(request))
    except ServiceError as exc:
        raise_service_error(exc)


@router.get("/applications", response_model=list[ApplicationResponse])
def list_applications(
    limit: int = 50,
    status: str | None = None,
    worker_id: str | None = None,
    shift_id: str | None = None,
    service: ApplicationService = Depends(get_application_service),
    actor: ActorContext = Depends(get_actor_context),
) -> list[ApplicationResponse]:
    require_role(actor.role, {ActorRole.OPERATOR, ActorRole.WORKER})
    if actor.role == ActorRole.WORKER:
        effective_worker_id = actor.worker_profile_id or actor.user_id
        if worker_id is not None and worker_id != effective_worker_id:
            raise HTTPException(status_code=403, detail="Worker can only access their own applications.")
        worker_id = effective_worker_id
    account_id = actor.account_id if actor.role == ActorRole.OPERATOR else None
    operator_id = actor.user_id if actor.role == ActorRole.OPERATOR and account_id is None else None
    items = service.list_applications(limit, status, worker_id, operator_id, account_id, shift_id)
    return [_application_view(item) for item in items]


@router.post("/applications/{application_id}/approve", response_model=ApplicationResponse, responses={400: {"model": ErrorResponse}, 404: {"model": ErrorResponse}})
def approve_application(
    application_id: str,
    request: ApplicationDecisionRequest,
    service: ApplicationService = Depends(get_application_service),
    notification_repo: NotificationRepository = Depends(get_notification_repo),
    actor: ActorContext = Depends(get_actor_context),
) -> ApplicationResponse:
    require_role(actor.role, {ActorRole.OPERATOR})
    try:
        _require_application_access(actor, service.get_application(application_id))
        application = service.approve_application(application_id, request)
        _notify_decision(notification_repo, application, "approved")
        return _application_view(application)
    except ServiceError as exc:
        raise_service_error(exc)


@router.post("/applications/{application_id}/reject", response_model=ApplicationResponse, responses={400: {"model": ErrorResponse}, 404: {"model": ErrorResponse}})
def reject_application(
    application_id: str,
    request: ApplicationDecisionRequest,
    service: ApplicationService = Depends(get_application_service),
    notification_repo: NotificationRepository = Depends(get_notification_repo),
    actor: ActorContext = Depends(get_actor_context),
) -> ApplicationResponse:
    require_role(actor.role, {ActorRole.OPERATOR})
    try:
        _require_application_access(actor, service.get_application(application_id))
        application = service.reject_application(application_id, request)
        _notify_decision(notification_repo, application, "rejected")
        return _application_view(application)
    except ServiceError as exc:
        raise_service_error(exc)


@router.put("/applications/{application_id}/message", response_model=ApplicationResponse, responses={400: {"model": ErrorResponse}, 404: {"model": ErrorResponse}})
def update_application_message(
    application_id: str,
    request: ApplicationMessageUpdateRequest,
    service: ApplicationService = Depends(get_application_service),
    actor: ActorContext = Depends(get_actor_context),
) -> ApplicationResponse:
    try:
        _require_application_access(actor, service.get_application(application_id))
        return _application_view(service.update_message(application_id, request))
    except ServiceError as exc:
        raise_service_error(exc)


@router.get("/applications/{application_id}/message-history", response_model=list[ApplicationMessageHistoryResponse], responses={404: {"model": ErrorResponse}})
def get_application_message_history(
    application_id: str,
    service: ApplicationService = Depends(get_application_service),
    actor: ActorContext = Depends(get_actor_context),
) -> list[ApplicationMessageHistoryResponse]:
    try:
        _require_application_access(actor, service.get_application(application_id))
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


def _require_application_access(actor: ActorContext, application: Application) -> None:
    require_role(actor.role, {ActorRole.OPERATOR, ActorRole.WORKER})
    effective_worker_id = actor.worker_profile_id or actor.user_id
    if actor.role == ActorRole.WORKER and application.worker_id != effective_worker_id:
        raise HTTPException(status_code=403, detail="Worker can only access their own applications.")
    if actor.role == ActorRole.OPERATOR and application.operator_id != actor.user_id:
        raise HTTPException(status_code=403, detail="Operator can only access their own applications.")

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response

from apps.api.src.auth import ActorContext, ActorRole, get_actor_context, require_role, require_verified_actor
from apps.api.src.deps import get_event_recorder, get_idempotency_service, get_message_service
from apps.api.src.models.message import MessageThreadView, MessageView
from apps.api.src.rate_limit import actor_or_ip, limiter
from apps.api.src.routes.idempotency_support import IdempotencyKeyHeader, replayed
from apps.api.src.routes.service_errors import raise_service_error
from apps.api.src.schemas import (
    ErrorResponse,
    MessageResponse,
    MessageSendRequest,
    MessageThreadReadRequest,
    MessageThreadResponse,
)
from apps.api.src.services.errors import ServiceError
from apps.api.src.services.event_recorder import EventRecorder
from apps.api.src.services.idempotency import IdempotencyConflict, IdempotencyService
from apps.api.src.services.message_service import MessageService

router = APIRouter(tags=["messages"])


@router.post(
    "/shifts/{shift_id}/messages",
    response_model=MessageResponse,
    responses={400: {"model": ErrorResponse}, 404: {"model": ErrorResponse}},
)
@limiter.limit("30/minute", key_func=actor_or_ip)
def send_message(
    shift_id: str,
    request: Request,
    payload: MessageSendRequest,
    response: Response,
    idempotency_key: IdempotencyKeyHeader = None,
    idempotency: IdempotencyService = Depends(get_idempotency_service),
    service: MessageService = Depends(get_message_service),
    actor: ActorContext = Depends(get_actor_context),
    recorder: EventRecorder = Depends(get_event_recorder),
) -> MessageResponse:
    try:
        require_verified_actor(actor, "sending messages")
        started = idempotency.start(
            actor.user_id,
            "message.create",
            idempotency_key,
            {"shift_id": shift_id, **payload.model_dump(mode="json")},
        )
        if started.cached_response is not None:
            return replayed(response, MessageResponse, started.cached_response)
        message = service.send_message(shift_id, payload, actor)
        result = _message_response(message)
        _record_message(recorder, actor, message)
        idempotency.finish(started.record_id, result.model_dump(mode="json"))
        return result
    except IdempotencyConflict as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    except ServiceError as exc:
        raise_service_error(exc)


@router.get("/shifts/{shift_id}/messages", response_model=list[MessageResponse])
def get_shift_messages(
    shift_id: str,
    limit: int = Query(default=100, ge=1, le=100),
    application_id: str | None = None,
    booking_id: str | None = None,
    service: MessageService = Depends(get_message_service),
    actor: ActorContext = Depends(get_actor_context),
) -> list[MessageResponse]:
    try:
        messages = service.list_messages(shift_id, actor, application_id, booking_id, limit)
        return [_message_response(message) for message in messages]
    except ServiceError as exc:
        raise_service_error(exc)


@router.post("/shifts/{shift_id}/messages/read", responses={404: {"model": ErrorResponse}})
def mark_thread_read(
    shift_id: str,
    payload: MessageThreadReadRequest,
    service: MessageService = Depends(get_message_service),
    actor: ActorContext = Depends(get_actor_context),
) -> dict:
    try:
        marked = service.mark_direct_read(shift_id, actor, payload.application_id, payload.booking_id)
    except ServiceError as exc:
        raise_service_error(exc)
    return {"status": "read", "shift_id": shift_id, "marked": marked}


@router.get("/shifts/{shift_id}/group-thread", response_model=MessageThreadResponse)
def get_group_thread(
    shift_id: str,
    limit: int = Query(default=100, ge=1, le=100),
    service: MessageService = Depends(get_message_service),
    actor: ActorContext = Depends(get_actor_context),
) -> MessageThreadResponse:
    try:
        return _thread_response(service.group_thread(shift_id, actor, limit))
    except ServiceError as exc:
        raise_service_error(exc)


@router.post("/shifts/{shift_id}/group-thread/messages", response_model=MessageResponse)
@limiter.limit("30/minute", key_func=actor_or_ip)
def send_group_message(
    shift_id: str,
    request: Request,
    payload: MessageSendRequest,
    service: MessageService = Depends(get_message_service),
    actor: ActorContext = Depends(get_actor_context),
    recorder: EventRecorder = Depends(get_event_recorder),
) -> MessageResponse:
    try:
        require_verified_actor(actor, "sending messages")
        message = service.send_group_message(shift_id, payload.content, actor)
        _record_message(recorder, actor, message)
        return _message_response(message)
    except ServiceError as exc:
        raise_service_error(exc)


@router.post("/shifts/{shift_id}/group-thread/read")
def mark_group_thread_read(
    shift_id: str,
    service: MessageService = Depends(get_message_service),
    actor: ActorContext = Depends(get_actor_context),
) -> dict:
    try:
        marked = service.mark_group_read(shift_id, actor)
    except ServiceError as exc:
        raise_service_error(exc)
    return {"status": "read", "shift_id": shift_id, "marked": marked}


@router.get("/me/employment-threads", response_model=list[MessageThreadResponse])
def worker_employment_threads(
    service: MessageService = Depends(get_message_service),
    actor: ActorContext = Depends(get_actor_context),
) -> list[MessageThreadResponse]:
    require_role(actor.role, {ActorRole.WORKER})
    try:
        return [_thread_response(thread) for thread in service.employment_threads(actor)]
    except ServiceError as exc:
        raise_service_error(exc)


@router.get("/venues/me/employment-threads", response_model=list[MessageThreadResponse])
def venue_employment_threads(
    service: MessageService = Depends(get_message_service),
    actor: ActorContext = Depends(get_actor_context),
) -> list[MessageThreadResponse]:
    require_role(actor.role, {ActorRole.OPERATOR})
    try:
        return [_thread_response(thread) for thread in service.employment_threads(actor)]
    except ServiceError as exc:
        raise_service_error(exc)


@router.get("/employment-threads/{relationship_id}", response_model=MessageThreadResponse)
def get_employment_thread(
    relationship_id: str,
    limit: int = Query(default=100, ge=1, le=100),
    service: MessageService = Depends(get_message_service),
    actor: ActorContext = Depends(get_actor_context),
) -> MessageThreadResponse:
    try:
        return _thread_response(service.employment_thread(relationship_id, actor, limit))
    except ServiceError as exc:
        raise_service_error(exc)


@router.post("/employment-threads/{relationship_id}/messages", response_model=MessageResponse)
@limiter.limit("30/minute", key_func=actor_or_ip)
def send_employment_message(
    relationship_id: str,
    request: Request,
    payload: MessageSendRequest,
    service: MessageService = Depends(get_message_service),
    actor: ActorContext = Depends(get_actor_context),
    recorder: EventRecorder = Depends(get_event_recorder),
) -> MessageResponse:
    try:
        require_verified_actor(actor, "sending messages")
        message = service.send_employment_message(relationship_id, payload.content, actor)
        _record_message(recorder, actor, message)
        return _message_response(message)
    except ServiceError as exc:
        raise_service_error(exc)


@router.post("/employment-threads/{relationship_id}/read")
def mark_employment_thread_read(
    relationship_id: str,
    service: MessageService = Depends(get_message_service),
    actor: ActorContext = Depends(get_actor_context),
) -> dict:
    try:
        marked = service.mark_employment_read(relationship_id, actor)
    except ServiceError as exc:
        raise_service_error(exc)
    return {"status": "read", "relationship_id": relationship_id, "marked": marked}


@router.get(
    "/venues/me/messages/export",
    summary="Export the active venue's immutable message record for scoped operators",
)
def export_messages(
    month: str = Query(..., pattern=r"^\d{4}-\d{2}$"),
    service: MessageService = Depends(get_message_service),
    actor: ActorContext = Depends(get_actor_context),
) -> Response:
    require_role(actor.role, {ActorRole.OPERATOR})
    if not actor.account_id:
        raise HTTPException(status_code=403, detail="This account is not linked to a venue.")
    try:
        body = service.export_csv(actor.account_id, month)
    except ServiceError as exc:
        raise_service_error(exc)
    return Response(
        content=body,
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="messages-{month}.csv"'},
    )


@router.post("/messages/{message_id}/read", responses={404: {"model": ErrorResponse}})
def mark_message_as_read(
    message_id: str,
    service: MessageService = Depends(get_message_service),
    actor: ActorContext = Depends(get_actor_context),
) -> dict:
    try:
        service.mark_as_read(message_id, actor)
    except ServiceError as exc:
        raise_service_error(exc)
    return {"status": "read", "message_id": message_id}


def _message_response(message: MessageView) -> MessageResponse:
    return MessageResponse(**message.model_dump())


def _thread_response(view: MessageThreadView) -> MessageThreadResponse:
    thread = view.thread
    return MessageThreadResponse(
        thread_id=thread.thread_id,
        kind=thread.kind,
        venue_id=thread.venue_id,
        shift_id=thread.shift_id,
        application_id=thread.application_id,
        booking_id=thread.booking_id,
        relationship_id=thread.relationship_id,
        worker_id=thread.worker_id,
        role=thread.role_snapshot,
        venue_name=thread.venue_name_snapshot,
        created_at=thread.created_at,
        can_post=view.can_post,
        messages=[_message_response(message) for message in view.messages],
    )


def _record_message(recorder: EventRecorder, actor: ActorContext, message: MessageView) -> None:
    recorder.record(
        "message.created",
        "audit",
        actor=actor,
        worker_id=actor.effective_worker_id if actor.role == ActorRole.WORKER else None,
        subject_type="message",
        subject_id=message.message_id,
        context={
            "thread_id": message.thread_id,
            "thread_kind": message.thread_kind,
            "shift_id": message.shift_id,
            "relationship_id": message.relationship_id,
        },
    )

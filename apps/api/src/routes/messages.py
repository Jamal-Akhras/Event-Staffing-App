from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response
from apps.api.src.auth import ActorContext, get_actor_context, require_verified_actor
from apps.api.src.deps import get_idempotency_service, get_message_service
from apps.api.src.rate_limit import actor_or_ip, limiter
from apps.api.src.routes.idempotency_support import IdempotencyKeyHeader, replayed
from apps.api.src.routes.service_errors import raise_service_error
from apps.api.src.schemas import ErrorResponse, MessageResponse, MessageSendRequest, MessageThreadReadRequest
from apps.api.src.services.errors import ServiceError
from apps.api.src.services.message_service import MessageService
from apps.api.src.services.idempotency import IdempotencyConflict, IdempotencyService

router = APIRouter(tags=["messages"])


@router.post("/shifts/{shift_id}/messages", response_model=MessageResponse, responses={400: {"model": ErrorResponse}, 404: {"model": ErrorResponse}})
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
        result = MessageResponse(**message.model_dump())
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
        return [MessageResponse(**msg.model_dump()) for msg in messages]
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
        marked = service.mark_thread_read(shift_id, actor, payload.application_id, payload.booking_id)
    except ServiceError as exc:
        raise_service_error(exc)
    return {"status": "read", "shift_id": shift_id, "marked": marked}


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

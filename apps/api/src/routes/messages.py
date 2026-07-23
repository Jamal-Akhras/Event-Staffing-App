from __future__ import annotations

from fastapi import APIRouter, Depends
from apps.api.src.auth import ActorContext, get_actor_context
from apps.api.src.deps import get_message_service
from apps.api.src.routes.service_errors import raise_service_error
from apps.api.src.schemas import ErrorResponse, MessageResponse, MessageSendRequest
from apps.api.src.services.errors import ServiceError
from apps.api.src.services.message_service import MessageService

router = APIRouter(tags=["messages"])


@router.post("/shifts/{shift_id}/messages", response_model=MessageResponse, responses={400: {"model": ErrorResponse}, 404: {"model": ErrorResponse}})
def send_message(
    shift_id: str,
    request: MessageSendRequest,
    service: MessageService = Depends(get_message_service),
    actor: ActorContext = Depends(get_actor_context),
) -> MessageResponse:
    try:
        message = service.send_message(
            shift_id,
            request,
            actor.role.value,
            actor.user_id,
        )
        return MessageResponse(**message.model_dump())
    except ServiceError as exc:
        raise_service_error(exc)


@router.get("/shifts/{shift_id}/messages", response_model=list[MessageResponse])
def get_shift_messages(
    shift_id: str,
    application_id: str | None = None,
    booking_id: str | None = None,
    service: MessageService = Depends(get_message_service),
    actor: ActorContext = Depends(get_actor_context),
) -> list[MessageResponse]:
    try:
        messages = service.list_messages(shift_id, actor.role.value, actor.user_id, application_id, booking_id)
        return [MessageResponse(**msg.model_dump()) for msg in messages]
    except ServiceError as exc:
        raise_service_error(exc)


@router.post("/messages/{message_id}/read", responses={404: {"model": ErrorResponse}})
def mark_message_as_read(
    message_id: str,
    service: MessageService = Depends(get_message_service),
    actor: ActorContext = Depends(get_actor_context),
) -> dict:
    try:
        service.mark_as_read(message_id, actor.role.value, actor.user_id)
    except ServiceError as exc:
        raise_service_error(exc)
    return {"status": "read", "message_id": message_id}

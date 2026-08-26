from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from apps.api.src.auth.dependencies import ActorContext, ActorRole, get_actor_context, require_worker_owner
from apps.api.src.deps import get_notification_repo, get_request_session
from apps.api.src.repositories.notification_repository import NotificationRepository
from apps.api.src.schemas_notifications import (
    NotificationActionResponse,
    NotificationPageResponse,
    NotificationPreferencesResponse,
    NotificationResponse,
    PushTokenRequest,
    PushTokenResponse,
)
from apps.api.src.services.notification_cursor import decode_notification_cursor, encode_notification_cursor
from apps.api.src.services.notification_settings import (
    delete_push_token,
    get_preferences,
    register_push_token,
    save_preferences,
)

router = APIRouter(tags=["notifications"])


@router.get("/notifications", response_model=NotificationPageResponse)
def list_actor_notifications(
    limit: int = Query(default=50, ge=1, le=100),
    cursor: str | None = None,
    repo: NotificationRepository = Depends(get_notification_repo),
    actor: ActorContext = Depends(get_actor_context),
) -> NotificationPageResponse:
    recipient_kind, recipient_id = _recipient(actor)
    try:
        decoded = decode_notification_cursor(cursor)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    rows = repo.list_for_recipient(recipient_kind, recipient_id, limit + 1, decoded)
    has_more = len(rows) > limit
    items = rows[:limit]
    next_cursor = (
        encode_notification_cursor(items[-1].created_at, items[-1].notification_id)
        if has_more and items
        else None
    )
    return NotificationPageResponse(
        items=[_view(item) for item in items],
        next_cursor=next_cursor,
        unread_count=repo.unread_count(recipient_kind, recipient_id),
    )


@router.post("/notifications/{notification_id}/read")
def mark_notification_read(
    notification_id: str,
    repo: NotificationRepository = Depends(get_notification_repo),
    actor: ActorContext = Depends(get_actor_context),
) -> dict[str, bool]:
    recipient_kind, recipient_id = _recipient(actor)
    if not repo.mark_read(notification_id, recipient_kind, recipient_id):
        raise HTTPException(status_code=404, detail="Notification not found.")
    return {"read": True}


@router.post("/notifications/read-all")
def mark_actor_notifications_read(
    repo: NotificationRepository = Depends(get_notification_repo),
    actor: ActorContext = Depends(get_actor_context),
) -> dict[str, int]:
    recipient_kind, recipient_id = _recipient(actor)
    return {"marked_read": repo.mark_all_read_for_recipient(recipient_kind, recipient_id)}


@router.get("/notification-preferences", response_model=NotificationPreferencesResponse)
def read_notification_preferences(
    session: Session | None = Depends(get_request_session),
    actor: ActorContext = Depends(get_actor_context),
) -> NotificationPreferencesResponse:
    channels, categories = get_preferences(session, actor.user_id)
    return NotificationPreferencesResponse(channels=channels, categories=categories)


@router.put("/notification-preferences", response_model=NotificationPreferencesResponse)
def update_notification_preferences(
    request: NotificationPreferencesResponse,
    session: Session | None = Depends(get_request_session),
    actor: ActorContext = Depends(get_actor_context),
) -> NotificationPreferencesResponse:
    try:
        channels, categories = save_preferences(
            session,
            actor.user_id,
            request.channels,
            request.categories,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return NotificationPreferencesResponse(channels=channels, categories=categories)


@router.post("/devices/push-tokens", response_model=PushTokenResponse)
def create_push_token(
    request: PushTokenRequest,
    session: Session | None = Depends(get_request_session),
    actor: ActorContext = Depends(get_actor_context),
) -> PushTokenResponse:
    try:
        saved = register_push_token(
            session,
            actor.user_id,
            request.token,
            request.platform,
            request.device_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return PushTokenResponse(
        push_token_id=saved.push_token_id,
        platform=saved.platform,
        device_id=saved.device_id,
    )


@router.delete("/devices/push-tokens/{push_token_id}")
def remove_push_token(
    push_token_id: str,
    session: Session | None = Depends(get_request_session),
    actor: ActorContext = Depends(get_actor_context),
) -> dict[str, bool]:
    if not delete_push_token(session, actor.user_id, push_token_id):
        raise HTTPException(status_code=404, detail="Push token not found.")
    return {"deleted": True}


@router.get("/workers/{worker_id}/notifications", response_model=list[NotificationResponse])
def list_worker_notifications_legacy(
    worker_id: str,
    limit: int = 50,
    repo: NotificationRepository = Depends(get_notification_repo),
    actor: ActorContext = Depends(get_actor_context),
) -> list[NotificationResponse]:
    require_worker_owner(actor, worker_id)
    return [_view(item) for item in repo.list_for_worker(worker_id, limit)]


@router.post("/workers/{worker_id}/notifications/read-all")
def mark_worker_notifications_read_legacy(
    worker_id: str,
    repo: NotificationRepository = Depends(get_notification_repo),
    actor: ActorContext = Depends(get_actor_context),
) -> dict[str, int]:
    require_worker_owner(actor, worker_id)
    return {"marked_read": repo.mark_all_read(worker_id)}


def _recipient(actor: ActorContext) -> tuple[str, str]:
    if actor.role == ActorRole.WORKER:
        return "worker", actor.effective_worker_id
    if actor.role == ActorRole.OPERATOR and actor.account_id:
        return "venue", actor.account_id
    raise HTTPException(status_code=403, detail="Actor has no notification inbox.")


def _view(notification) -> NotificationResponse:
    action = None
    if notification.action_kind and notification.action_entity_id:
        action = NotificationActionResponse(
            kind=notification.action_kind,
            entity_id=notification.action_entity_id,
        )
    return NotificationResponse(
        notification_id=notification.notification_id,
        type=notification.type,
        title=notification.title,
        body=notification.body,
        action=action,
        read=notification.read,
        created_at=notification.created_at,
    )

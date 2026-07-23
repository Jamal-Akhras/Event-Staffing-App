from __future__ import annotations

from fastapi import APIRouter, Depends

from apps.api.src.auth.dependencies import ActorContext, ActorRole, get_actor_context, require_role, require_worker_owner
from apps.api.src.deps import get_notification_repo
from apps.api.src.repositories.notification_repository import NotificationRepository
from apps.api.src.schemas_notifications import NotificationResponse

router = APIRouter(tags=["notifications"])


@router.get("/workers/{worker_id}/notifications", response_model=list[NotificationResponse])
def list_notifications(
    worker_id: str,
    limit: int = 50,
    repo: NotificationRepository = Depends(get_notification_repo),
    actor: ActorContext = Depends(get_actor_context),
) -> list[NotificationResponse]:
    require_worker_owner(actor, worker_id)
    items = repo.list_for_worker(worker_id, limit)
    return [
        NotificationResponse(
            notification_id=n.notification_id,
            type=n.type,
            title=n.title,
            body=n.body,
            shift_id=n.shift_id,
            read=n.read,
            created_at=n.created_at,
        )
        for n in items
    ]


@router.post("/workers/{worker_id}/notifications/read-all")
def mark_all_read(
    worker_id: str,
    repo: NotificationRepository = Depends(get_notification_repo),
    actor: ActorContext = Depends(get_actor_context),
) -> dict[str, int]:
    require_worker_owner(actor, worker_id)
    count = repo.mark_all_read(worker_id)
    return {"marked_read": count}

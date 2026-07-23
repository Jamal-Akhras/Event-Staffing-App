from __future__ import annotations

from fastapi import APIRouter, Depends

from apps.api.src.auth import ActorContext, get_actor_context, require_worker_owner
from apps.api.src.deps import get_worker_feed_service
from apps.api.src.routes.service_errors import raise_service_error
from apps.api.src.schemas import (
    ErrorResponse,
    WorkerFeedStateResponse,
    WorkerFeedStateUpdateRequest,
)
from apps.api.src.services.errors import ServiceError
from apps.api.src.services.worker_feed_service import WorkerFeedService

router = APIRouter(tags=["worker feed"])


@router.get("/workers/{worker_id}/feed-state", response_model=list[WorkerFeedStateResponse])
def list_feed_state(
    worker_id: str,
    service: WorkerFeedService = Depends(get_worker_feed_service),
    actor: ActorContext = Depends(get_actor_context),
) -> list[WorkerFeedStateResponse]:
    require_worker_owner(actor, worker_id)
    return [WorkerFeedStateResponse(**item.model_dump()) for item in service.list_state(worker_id)]


@router.put(
    "/workers/{worker_id}/feed-state/{shift_id}",
    response_model=WorkerFeedStateResponse,
    responses={400: {"model": ErrorResponse}, 404: {"model": ErrorResponse}},
)
def save_feed_state(
    worker_id: str,
    shift_id: str,
    request: WorkerFeedStateUpdateRequest,
    service: WorkerFeedService = Depends(get_worker_feed_service),
    actor: ActorContext = Depends(get_actor_context),
) -> WorkerFeedStateResponse:
    require_worker_owner(actor, worker_id)
    try:
        return WorkerFeedStateResponse(
            **service.save_state(worker_id, shift_id, request).model_dump()
        )
    except ServiceError as exc:
        raise_service_error(exc)


@router.delete("/workers/{worker_id}/feed-state/{shift_id}")
def delete_feed_state(
    worker_id: str,
    shift_id: str,
    service: WorkerFeedService = Depends(get_worker_feed_service),
    actor: ActorContext = Depends(get_actor_context),
) -> dict[str, str]:
    require_worker_owner(actor, worker_id)
    service.delete_state(worker_id, shift_id)
    return {"status": "deleted", "shift_id": shift_id}

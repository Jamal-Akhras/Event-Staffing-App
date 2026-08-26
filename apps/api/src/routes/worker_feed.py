from __future__ import annotations

from decimal import Decimal
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query

from apps.api.src.auth import ActorContext, ActorRole, get_actor_context, require_role, require_worker_owner
from apps.api.src.deps import get_worker_feed_service, get_worker_shift_feed_service
from apps.api.src.helpers import _shift_view
from apps.api.src.routes.service_errors import raise_service_error
from apps.api.src.schemas import (
    ErrorResponse,
    WorkerFeedStateResponse,
    WorkerFeedStateUpdateRequest,
)
from apps.api.src.services.errors import ServiceError
from apps.api.src.schemas_market import MarketResponse
from apps.api.src.schemas_worker_feed import (
    FeedVenueResponse,
    WorkerFeedItemResponse,
    WorkerFeedPageResponse,
)
from apps.api.src.services.worker_feed_cursor import FeedCursorError
from apps.api.src.services.worker_feed_service import WorkerFeedService
from apps.api.src.services.worker_shift_feed_service import WorkerMarketMissingError, WorkerShiftFeedService

router = APIRouter(tags=["worker feed"])


@router.get("/workers/me/feed", response_model=WorkerFeedPageResponse)
def list_worker_feed(
    limit: int = Query(default=20, ge=1, le=50),
    cursor: str | None = Query(default=None, max_length=2048),
    search_query: str | None = Query(default=None, alias="query", max_length=100),
    timing: Literal["all", "today", "weekend"] = "all",
    minimum_pay: Decimal | None = Query(
        default=None,
        ge=0,
        max_digits=12,
        decimal_places=2,
    ),
    service: WorkerShiftFeedService = Depends(get_worker_shift_feed_service),
    actor: ActorContext = Depends(get_actor_context),
) -> WorkerFeedPageResponse:
    require_role(actor.role, {ActorRole.WORKER})
    worker_id = actor.effective_worker_id
    try:
        page = service.list_page(
            worker_id=worker_id,
            limit=limit,
            cursor=cursor,
            search=search_query,
            timing=timing,
            minimum_pay=minimum_pay,
        )
    except WorkerMarketMissingError as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    except FeedCursorError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    return WorkerFeedPageResponse(
        items=[
            WorkerFeedItemResponse(
                **_shift_view(item.shift).model_dump(),
                venue=FeedVenueResponse(
                    venue_id=item.venue.venue_id,
                    name=item.venue.name,
                    avatar_url=item.venue.avatar_url,
                ),
            )
            for item in page.items
        ],
        next_cursor=page.next_cursor,
        market=MarketResponse.from_domain(page.market),
    )


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

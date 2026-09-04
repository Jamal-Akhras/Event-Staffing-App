from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field

from apps.api.src.auth import ActorContext, ActorRole, get_actor_context, require_role
from apps.api.src.datetime_utils import utc_now
from apps.api.src.deps import get_feed_appeal_service
from apps.api.src.models.feed_ranking_appeal import FeedRankingAppeal
from apps.api.src.routes.service_errors import raise_service_error
from apps.api.src.services.errors import ServiceError
from apps.api.src.services.feed_appeal_service import FeedAppealService
from apps.api.src.validation_types import UtcTimestamp

router = APIRouter(tags=["feed ranking"])


class AppealCreateRequest(BaseModel):
    shift_id: str = Field(min_length=1, max_length=100)
    slate_id: str | None = Field(default=None, max_length=100)
    reason: str = Field(min_length=3, max_length=1000)


class AppealReviewRequest(BaseModel):
    outcome_note: str = Field(min_length=3, max_length=1000)


class AppealResponse(BaseModel):
    appeal_id: str
    worker_id: str
    shift_id: str
    slate_id: str | None
    reason: str
    created_at: UtcTimestamp
    reviewed_at: UtcTimestamp | None
    outcome_note: str | None


@router.post("/me/feed-appeals", response_model=AppealResponse, status_code=201)
def file_appeal(
    payload: AppealCreateRequest,
    actor: ActorContext = Depends(get_actor_context),
    service: FeedAppealService = Depends(get_feed_appeal_service),
) -> AppealResponse:
    require_role(actor.role, {ActorRole.WORKER})
    appeal = service.file(
        actor.effective_worker_id, payload.shift_id, payload.slate_id, payload.reason, utc_now()
    )
    return _view(appeal)


@router.get("/me/feed-appeals", response_model=list[AppealResponse])
def list_my_appeals(
    actor: ActorContext = Depends(get_actor_context),
    service: FeedAppealService = Depends(get_feed_appeal_service),
) -> list[AppealResponse]:
    require_role(actor.role, {ActorRole.WORKER})
    return [_view(appeal) for appeal in service.list_for_worker(actor.effective_worker_id)]


@router.get("/system/feed-appeals", response_model=list[AppealResponse])
def list_open_appeals(
    limit: int = Query(default=100, ge=1, le=500),
    actor: ActorContext = Depends(get_actor_context),
    service: FeedAppealService = Depends(get_feed_appeal_service),
) -> list[AppealResponse]:
    require_role(actor.role, {ActorRole.SYSTEM})
    return [_view(appeal) for appeal in service.list_open(limit)]


@router.post("/system/feed-appeals/{appeal_id}/review", response_model=AppealResponse)
def review_appeal(
    appeal_id: str,
    payload: AppealReviewRequest,
    actor: ActorContext = Depends(get_actor_context),
    service: FeedAppealService = Depends(get_feed_appeal_service),
) -> AppealResponse:
    require_role(actor.role, {ActorRole.SYSTEM})
    try:
        appeal = service.review(appeal_id, actor.user_id, payload.outcome_note, utc_now())
    except ServiceError as exc:
        raise_service_error(exc)
    return _view(appeal)


def _view(appeal: FeedRankingAppeal) -> AppealResponse:
    return AppealResponse(
        appeal_id=appeal.appeal_id,
        worker_id=appeal.worker_id,
        shift_id=appeal.shift_id,
        slate_id=appeal.slate_id,
        reason=appeal.reason,
        created_at=appeal.created_at,
        reviewed_at=appeal.reviewed_at,
        outcome_note=appeal.outcome_note,
    )

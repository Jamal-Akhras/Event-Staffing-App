from __future__ import annotations

from apps.api.src.validation_types import UtcTimestamp
from pydantic import BaseModel, Field

from apps.api.src.schemas import ShiftResponse
from apps.api.src.schemas_market import MarketResponse


class FeedVenueResponse(BaseModel):
    venue_id: str
    name: str
    avatar_url: str | None


class WorkerFeedItemResponse(ShiftResponse):
    venue: FeedVenueResponse


class WorkerFeedPageResponse(BaseModel):
    items: list[WorkerFeedItemResponse]
    slate_id: str
    next_cursor: str | None
    market: MarketResponse


class WorkerFeedStateUpdateRequest(BaseModel):
    action: str = Field(pattern="^passed$")
    now: UtcTimestamp | None = None


class WorkerFeedStateResponse(BaseModel):
    worker_id: str
    shift_id: str
    action: str
    created_at: UtcTimestamp
    updated_at: UtcTimestamp

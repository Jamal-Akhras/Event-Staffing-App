from __future__ import annotations

from pydantic import BaseModel

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

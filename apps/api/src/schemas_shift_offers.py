from __future__ import annotations

from typing import Literal

from pydantic import BaseModel

from apps.api.src.schemas_shift_summary import ShiftSummaryResponse
from apps.api.src.validation_types import UtcTimestamp


class ShiftOfferResponse(BaseModel):
    offer_id: str
    shift_id: str
    venue_id: str
    worker_id: str
    source: Literal["rota", "cover", "manual"]
    status: Literal["pending", "accepted", "declined", "withdrawn", "expired"]
    offered_at: UtcTimestamp
    expires_at: UtcTimestamp | None
    responded_at: UtcTimestamp | None
    response_source: Literal["manual", "auto"] | None
    shift: ShiftSummaryResponse | None = None


class OfferAnswerRequest(BaseModel):
    now: UtcTimestamp | None = None

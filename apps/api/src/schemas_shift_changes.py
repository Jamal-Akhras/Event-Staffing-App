from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, model_validator

from apps.api.src.schemas_shift_summary import ShiftSummaryResponse
from apps.api.src.validation_types import UtcTimestamp


class ShiftChangeCreateRequest(BaseModel):
    booking_id: str = Field(min_length=1, max_length=100)
    change_type: Literal["release", "cover"]
    reason: str = Field(min_length=3, max_length=500)
    replacement_worker_id: str | None = Field(default=None, max_length=100)
    now: UtcTimestamp | None = None

    @model_validator(mode="after")
    def validate_replacement(self) -> "ShiftChangeCreateRequest":
        if self.change_type == "cover" and not self.replacement_worker_id:
            raise ValueError("A cover request names its replacement worker.")
        if self.change_type == "release" and self.replacement_worker_id:
            raise ValueError("A release request has no replacement worker.")
        return self


class ShiftChangeAnswerRequest(BaseModel):
    now: UtcTimestamp | None = None


class ShiftChangeResponse(BaseModel):
    request_id: str
    booking_id: str
    shift_id: str
    venue_id: str
    worker_id: str
    change_type: Literal["release", "cover"]
    status: Literal[
        "pending_replacement", "pending_manager", "approved", "declined", "withdrawn", "expired"
    ]
    reason: str
    replacement_worker_id: str | None
    created_at: UtcTimestamp
    updated_at: UtcTimestamp
    decided_at: UtcTimestamp | None
    decided_by_user_id: str | None
    shift: ShiftSummaryResponse | None = None

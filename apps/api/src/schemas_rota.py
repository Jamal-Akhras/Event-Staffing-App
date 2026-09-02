from __future__ import annotations

from datetime import date
from typing import Literal

from pydantic import BaseModel, Field

from apps.api.src.validation_types import UtcTimestamp


class RotaPublishRequest(BaseModel):
    week_start: date
    now: UtcTimestamp | None = None


class RotaTimesRequest(BaseModel):
    start_time: UtcTimestamp
    end_time: UtcTimestamp
    now: UtcTimestamp | None = None


class RotaReassignRequest(BaseModel):
    worker_id: str = Field(min_length=1, max_length=100)
    now: UtcTimestamp | None = None


class RotaRemoveRequest(BaseModel):
    reason: str = Field(min_length=3, max_length=500)
    now: UtcTimestamp | None = None


class AssignmentEntry(BaseModel):
    shift_id: str
    worker_id: str
    role: str
    start_time: UtcTimestamp
    end_time: UtcTimestamp


class RotaChange(BaseModel):
    kind: Literal["added", "removed", "reassigned", "time_changed"]
    shift_id: str
    role: str
    worker_id: str | None = None
    previous_worker_id: str | None = None
    start_time: UtcTimestamp | None = None
    end_time: UtcTimestamp | None = None
    previous_start_time: UtcTimestamp | None = None
    previous_end_time: UtcTimestamp | None = None


class RotaPublicationResponse(BaseModel):
    publication_id: str
    venue_id: str
    week_start: date
    revision: int
    published_at: UtcTimestamp
    published_by_user_id: str
    assignments: list[AssignmentEntry]
    changes: list[RotaChange]


class RotaPublishResponse(BaseModel):
    publication: RotaPublicationResponse
    booked_worker_ids: list[str]
    offered_worker_ids: list[str]

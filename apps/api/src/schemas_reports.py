from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from apps.api.src.validation_types import UtcTimestamp

ReportSubject = Literal["venue", "shift", "application", "booking", "message"]
ReportCategory = Literal["safety", "harassment", "payment", "no_show", "fraud", "other"]
ReportStatus = Literal["submitted", "reviewing", "resolved", "dismissed"]


class ReportCreateRequest(BaseModel):
    subject_type: ReportSubject
    subject_id: str = Field(min_length=1, max_length=100)
    category: ReportCategory
    description: str = Field(min_length=10, max_length=2000)


class ReportReviewRequest(BaseModel):
    status: Literal["reviewing", "resolved", "dismissed"]
    resolution_notes: str | None = Field(default=None, max_length=2000)


class ReportResponse(BaseModel):
    report_id: str
    reporter_user_id: str
    reporter_role: str
    subject_type: str
    subject_id: str
    category: str
    description: str
    status: str
    resolution_notes: str | None
    created_at: UtcTimestamp
    updated_at: UtcTimestamp

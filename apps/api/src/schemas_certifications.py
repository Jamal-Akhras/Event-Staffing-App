from __future__ import annotations

from pydantic import BaseModel, Field

from apps.api.src.validation_types import UtcTimestamp


class CertificationUpsertRequest(BaseModel):
    display_name: str = Field(min_length=2, max_length=120)
    expires_at: UtcTimestamp
    reference: str | None = Field(default=None, max_length=120)
    now: UtcTimestamp | None = None


class CertificationResponse(BaseModel):
    certification_id: str
    name: str
    display_name: str
    expires_at: UtcTimestamp
    reference: str | None
    created_at: UtcTimestamp
    updated_at: UtcTimestamp

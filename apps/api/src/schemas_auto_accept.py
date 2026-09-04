from __future__ import annotations

from decimal import Decimal
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from apps.api.src.validation_types import UtcTimestamp


class AutoAcceptRuleUpsertRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    enabled: bool
    roles: list[str]
    minimum_rate: Decimal | None = Field(default=None, ge=0, le=10000)
    minimum_notice_hours: int | None = Field(default=None, ge=0, le=8760)
    now: UtcTimestamp | None = None


class AutoAcceptRuleResponse(BaseModel):
    rule_id: str
    worker_id: str
    venue_id: str
    enabled: bool
    roles: list[str]
    minimum_rate: Decimal | None
    minimum_notice_hours: int | None
    version: int
    created_at: UtcTimestamp
    updated_at: UtcTimestamp


class AutoAcceptAttemptResponse(BaseModel):
    attempt_id: str
    offer_id: str
    rule_id: str | None
    rule_version: int
    rule_snapshot: dict[str, Any]
    evaluated_at: UtcTimestamp
    outcome: Literal["accepted", "skipped", "failed"]
    reason: str | None

from __future__ import annotations

from decimal import Decimal
from typing import Literal

from pydantic import BaseModel

from apps.api.src.validation_types import UtcTimestamp


class MyRelationshipResponse(BaseModel):
    relationship_id: str
    venue_id: str
    venue_name: str | None
    relationship_type: str
    status: str
    default_role: str | None
    agreed_rate: Decimal | None
    contracted_hours_per_week: Decimal | None
    start_date: UtcTimestamp | None
    end_date: UtcTimestamp | None


class WorkerContextResponse(BaseModel):
    home_mode: Literal["shifts", "browse"]
    employed: bool
    active_relationships: int

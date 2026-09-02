from __future__ import annotations

from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field

from apps.api.src.validation_types import UtcTimestamp

EmployedType = Literal["permanent", "part_time", "bank"]


class JoinCodeCreateRequest(BaseModel):
    relationship_type: EmployedType
    max_redemptions: int = Field(default=1, ge=1, le=500)
    default_role: str | None = Field(default=None, max_length=80)
    expires_at: UtcTimestamp | None = None


class JoinCodeResponse(BaseModel):
    code: str
    venue_id: str
    relationship_type: str
    default_role: str | None
    max_redemptions: int
    redeemed: int
    expires_at: UtcTimestamp | None
    revoked_at: UtcTimestamp | None
    created_at: UtcTimestamp


class JoinCodePreviewResponse(BaseModel):
    code: str
    venue_name: str
    relationship_type: str
    default_role: str | None


class EmploymentInviteRequest(BaseModel):
    relationship_type: EmployedType
    default_role: str | None = Field(default=None, max_length=80)


class TermsUpdateRequest(BaseModel):
    agreed_rate: Decimal | None = Field(default=None, ge=0, le=10000)
    contracted_hours_per_week: Decimal | None = Field(default=None, ge=0, le=168)
    default_role: str | None = Field(default=None, max_length=80)


class EndRelationshipRequest(BaseModel):
    reason: str | None = Field(default=None, max_length=500)


class DirectoryEntryResponse(BaseModel):
    worker_id: str
    display_name: str
    role: str
    relationship_id: str
    relationship_type: str
    status: str
    agreed_rate: Decimal | None
    contracted_hours_per_week: Decimal | None
    start_date: UtcTimestamp | None
    end_date: UtcTimestamp | None
    reliability_score: float
    avatar_url: str | None
    allows_recontact: bool
    shifts_with_you: int
    hours_with_you: Decimal
    wages_to_date: Decimal
    fees_to_date: Decimal
    last_worked: UtcTimestamp | None


class InvitationResponse(BaseModel):
    relationship_id: str
    venue_id: str
    venue_name: str | None
    relationship_type: str
    default_role: str | None
    invited_at: UtcTimestamp


class WorkerRelationshipResponse(BaseModel):
    relationship_id: str
    venue_id: str
    worker_id: str
    relationship_type: str
    status: str
    default_role: str | None
    agreed_rate: Decimal | None = None
    contracted_hours_per_week: Decimal | None = None
    start_date: UtcTimestamp | None
    end_date: UtcTimestamp | None
    created_at: UtcTimestamp
    updated_at: UtcTimestamp

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from apps.api.src.auth.schemas import NormalizedEmail
from apps.api.src.validation_types import UtcTimestamp


class VenueCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=160)
    market_id: str = Field(min_length=1, max_length=100)
    venue_type: str | None = Field(default=None, max_length=80)
    default_location: str | None = Field(default=None, max_length=240)


class ManagerInviteRequest(BaseModel):
    email: NormalizedEmail
    role: Literal["admin", "manager"]
    venue_ids: list[str] | None = Field(default=None, max_length=50)


class MemberRoleUpdateRequest(BaseModel):
    role: Literal["owner", "admin", "manager"]
    venue_ids: list[str] | None = Field(default=None, max_length=50)


class InvitationAcceptRequest(BaseModel):
    token: str = Field(min_length=8, max_length=64)


class InvitedRegisterRequest(BaseModel):
    email: NormalizedEmail
    password: str = Field(min_length=8, max_length=128)
    token: str = Field(min_length=8, max_length=64)


class SwitchVenueRequest(BaseModel):
    venue_id: str = Field(min_length=1, max_length=100)


class MemberResponse(BaseModel):
    user_id: str
    email: str | None
    role: str
    venue_ids: list[str] | None
    created_at: UtcTimestamp


class InvitationResponse(BaseModel):
    invitation_id: str
    email: str
    role: str
    venue_ids: list[str] | None
    token: str
    expires_at: UtcTimestamp
    accepted_at: UtcTimestamp | None

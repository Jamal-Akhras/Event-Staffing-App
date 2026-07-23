from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from apps.api.src.services.notification_preferences import default_notification_preferences


class AccountResponse(BaseModel):
    account_id: str
    name: str
    country: str
    currency: str
    created_at: datetime
    venue_type: str | None = None
    contact_email: str | None = None
    contact_phone: str | None = None
    default_location: str | None = None
    avatar_url: str | None = None
    photos: list[str] = Field(default_factory=list)
    notification_preferences: dict[str, bool] = Field(default_factory=default_notification_preferences)


class AccountUpdateRequest(BaseModel):
    name: str | None = None
    venue_type: str | None = None
    contact_email: str | None = None
    contact_phone: str | None = None
    default_location: str | None = None
    avatar_url: str | None = None
    photos: list[str] | None = None
    notification_preferences: dict[str, bool] | None = None

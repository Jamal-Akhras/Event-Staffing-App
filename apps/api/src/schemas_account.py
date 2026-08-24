from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from apps.api.src.services.notification_preferences import default_notification_preferences
from apps.api.src.validation_types import UtcTimestamp


class AccountResponse(BaseModel):
    account_id: str
    venue_id: str
    organisation_id: str | None
    market_id: str | None
    name: str
    country: str
    currency: str
    created_at: UtcTimestamp
    venue_type: str | None = None
    contact_email: str | None = None
    contact_phone: str | None = None
    default_location: str | None = None
    avatar_url: str | None = None
    photos: list[str] = Field(default_factory=list)
    notification_preferences: dict[str, bool] = Field(default_factory=default_notification_preferences)


class AccountUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str | None = Field(default=None, min_length=1, max_length=160)
    venue_type: str | None = Field(default=None, max_length=120)
    contact_email: str | None = Field(default=None, max_length=254)
    contact_phone: str | None = Field(default=None, max_length=50)
    default_location: str | None = Field(default=None, max_length=240)
    photos: list[str] | None = Field(default=None, max_length=20)
    notification_preferences: dict[str, bool] | None = None
    market_id: str | None = Field(default=None, max_length=100)

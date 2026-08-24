from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from apps.api.src.services.notification_preferences import (
    NotificationPreferences,
    default_notification_preferences,
)

COUNTRY_CURRENCY = {"GB": "GBP", "AE": "AED"}


@dataclass(frozen=True)
class Account:
    account_id: str
    name: str
    country: str  # "GB" or "AE"
    currency: str  # "GBP" or "AED"
    created_at: datetime
    venue_type: str | None = None
    contact_email: str | None = None
    contact_phone: str | None = None
    default_location: str | None = None
    avatar_url: str | None = None
    photos: list[str] = field(default_factory=list)
    notification_preferences: NotificationPreferences = field(default_factory=default_notification_preferences)
    organisation_id: str | None = None
    market_id: str | None = None

    @property
    def venue_id(self) -> str:
        return self.account_id

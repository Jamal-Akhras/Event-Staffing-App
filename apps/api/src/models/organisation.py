from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from enum import Enum

from apps.api.src.services.notification_preferences import (
    NotificationPreferences,
    default_notification_preferences,
)


class OrganisationRole(str, Enum):
    OWNER = "owner"
    ADMIN = "admin"
    MANAGER = "manager"


@dataclass(frozen=True)
class Market:
    market_id: str
    name: str
    country: str
    currency: str
    timezone: str
    high_pay_threshold: Decimal
    is_active: bool
    created_at: datetime


@dataclass(frozen=True)
class Organisation:
    organisation_id: str
    name: str
    country: str
    currency: str
    created_at: datetime


@dataclass(frozen=True)
class Venue:
    venue_id: str
    organisation_id: str
    name: str
    country: str
    currency: str
    created_at: datetime
    venue_type: str | None = None
    contact_email: str | None = None
    contact_phone: str | None = None
    default_location: str | None = None
    avatar_url: str | None = None
    photos: list[str] = field(default_factory=list)
    notification_preferences: NotificationPreferences = field(default_factory=default_notification_preferences)
    market_id: str | None = None


@dataclass(frozen=True)
class OrganisationMembership:
    organisation_id: str
    user_id: str
    role: OrganisationRole
    created_at: datetime

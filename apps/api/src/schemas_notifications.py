from __future__ import annotations

from pydantic import BaseModel, Field

from apps.api.src.validation_types import UtcTimestamp


class NotificationActionResponse(BaseModel):
    kind: str
    entity_id: str


class NotificationResponse(BaseModel):
    notification_id: str
    type: str
    title: str
    body: str
    action: NotificationActionResponse | None = None
    read: bool
    created_at: UtcTimestamp


class NotificationPageResponse(BaseModel):
    items: list[NotificationResponse]
    next_cursor: str | None
    unread_count: int


class NotificationPreferencesResponse(BaseModel):
    channels: dict[str, bool]
    categories: dict[str, bool]


class PushTokenRequest(BaseModel):
    token: str = Field(min_length=1, max_length=500)
    platform: str = Field(pattern="^(ios|android)$")
    device_id: str = Field(min_length=1, max_length=200)


class PushTokenResponse(BaseModel):
    push_token_id: str
    platform: str
    device_id: str

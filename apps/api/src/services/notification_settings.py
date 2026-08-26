from __future__ import annotations

from dataclasses import dataclass
from uuid import uuid4

from sqlalchemy.orm import Session

from apps.api.src.datetime_utils import utc_now
from apps.api.src.db.notification_models import PushTokenModel, UserNotificationPreferenceModel

CHANNEL_DEFAULTS = {"in_app": True, "email": True, "push": True}
CATEGORY_DEFAULTS = {
    "applications": True,
    "shift_changes": True,
    "messages": True,
    "reminders": True,
    "attendance": True,
}

_MEMORY_PREFERENCES: dict[str, tuple[dict[str, bool], dict[str, bool]]] = {}
_MEMORY_TOKENS: dict[str, "PushToken"] = {}


@dataclass(frozen=True)
class PushToken:
    push_token_id: str
    user_id: str
    token: str
    platform: str
    device_id: str


def get_preferences(session: Session | None, user_id: str) -> tuple[dict[str, bool], dict[str, bool]]:
    if session is None:
        channels, categories = _MEMORY_PREFERENCES.get(
            user_id,
            (CHANNEL_DEFAULTS, CATEGORY_DEFAULTS),
        )
        return dict(channels), dict(categories)
    row = session.get(UserNotificationPreferenceModel, user_id)
    if row is None:
        return dict(CHANNEL_DEFAULTS), dict(CATEGORY_DEFAULTS)
    return normalize_flags(row.channels, CHANNEL_DEFAULTS), normalize_flags(row.categories, CATEGORY_DEFAULTS)


def save_preferences(
    session: Session | None,
    user_id: str,
    channels: dict[str, bool],
    categories: dict[str, bool],
) -> tuple[dict[str, bool], dict[str, bool]]:
    normalized_channels = _validate_complete(channels, CHANNEL_DEFAULTS, "channels")
    normalized_categories = _validate_complete(categories, CATEGORY_DEFAULTS, "categories")
    if session is None:
        _MEMORY_PREFERENCES[user_id] = (normalized_channels, normalized_categories)
        return dict(normalized_channels), dict(normalized_categories)
    row = session.get(UserNotificationPreferenceModel, user_id)
    if row is None:
        row = UserNotificationPreferenceModel(user_id=user_id)
        session.add(row)
    row.channels = normalized_channels
    row.categories = normalized_categories
    row.updated_at = utc_now()
    session.flush()
    return dict(normalized_channels), dict(normalized_categories)


def register_push_token(
    session: Session | None,
    user_id: str,
    token: str,
    platform: str,
    device_id: str,
) -> PushToken:
    if session is None:
        matches = [
            item
            for item in _MEMORY_TOKENS.values()
            if item.token == token or (item.user_id == user_id and item.device_id == device_id)
        ]
        existing = matches[0] if matches else None
        for item in matches[1:]:
            del _MEMORY_TOKENS[item.push_token_id]
        push_token_id = existing.push_token_id if existing else str(uuid4())
        saved = PushToken(push_token_id, user_id, token, platform, device_id)
        _MEMORY_TOKENS[push_token_id] = saved
        return saved
    token_row = session.query(PushTokenModel).filter(PushTokenModel.token == token).first()
    device_row = (
        session.query(PushTokenModel)
        .filter(PushTokenModel.user_id == user_id, PushTokenModel.device_id == device_id)
        .first()
    )
    if token_row and device_row and token_row.push_token_id != device_row.push_token_id:
        session.delete(device_row)
        session.flush()
    row = token_row or device_row
    now = utc_now()
    if row is None:
        row = PushTokenModel(push_token_id=str(uuid4()), created_at=now)
        session.add(row)
    row.user_id = user_id
    row.token = token.strip()
    row.platform = platform
    row.device_id = device_id.strip()
    row.updated_at = now
    row.last_seen_at = now
    row.revoked_at = None
    session.flush()
    return _to_push_token(row)


def delete_push_token(session: Session | None, user_id: str, push_token_id: str) -> bool:
    if session is None:
        item = _MEMORY_TOKENS.get(push_token_id)
        if item is None or item.user_id != user_id:
            return False
        del _MEMORY_TOKENS[push_token_id]
        return True
    count = (
        session.query(PushTokenModel)
        .filter(PushTokenModel.push_token_id == push_token_id, PushTokenModel.user_id == user_id)
        .delete(synchronize_session=False)
    )
    session.flush()
    return count == 1


def normalize_flags(raw: object, defaults: dict[str, bool]) -> dict[str, bool]:
    result = dict(defaults)
    if isinstance(raw, dict):
        for key in result:
            if isinstance(raw.get(key), bool):
                result[key] = raw[key]
    return result


def _validate_complete(raw: dict[str, bool], defaults: dict[str, bool], field: str) -> dict[str, bool]:
    if set(raw) != set(defaults):
        raise ValueError(f"{field} must include exactly: {', '.join(defaults)}.")
    return dict(raw)


def _to_push_token(row: PushTokenModel) -> PushToken:
    return PushToken(row.push_token_id, row.user_id, row.token, row.platform, row.device_id)

from __future__ import annotations

from sqlalchemy.orm import Session

from apps.api.src.db.models import UserModel
from apps.api.src.db.notification_models import PushTokenModel, UserNotificationPreferenceModel
from apps.api.src.services.notification_settings import CATEGORY_DEFAULTS, CHANNEL_DEFAULTS


def channel_enabled(session: Session, recipient: dict, channel: str, payload: dict) -> bool:
    if payload.get("transactional"):
        return True
    users = _recipient_users(session, recipient)
    if not users:
        return channel == "in_app"
    category = payload["category"]
    for user in users:
        preferences = session.get(UserNotificationPreferenceModel, user.user_id)
        channels = _normalized(preferences.channels if preferences else None, CHANNEL_DEFAULTS)
        categories = _normalized(preferences.categories if preferences else None, CATEGORY_DEFAULTS)
        if channels[channel] and categories[category]:
            return True
    return False


def push_tokens(session: Session, recipient_kind: str, recipient_id: str, payload: dict) -> list[str]:
    recipient = {"kind": recipient_kind, "id": recipient_id}
    users = _recipient_users(session, recipient)
    enabled_user_ids = []
    for user in users:
        preferences = session.get(UserNotificationPreferenceModel, user.user_id)
        channels = _normalized(preferences.channels if preferences else None, CHANNEL_DEFAULTS)
        categories = _normalized(preferences.categories if preferences else None, CATEGORY_DEFAULTS)
        if channels["push"] and categories[payload["category"]]:
            enabled_user_ids.append(user.user_id)
    if not enabled_user_ids:
        return []
    rows = (
        session.query(PushTokenModel.token)
        .filter(PushTokenModel.user_id.in_(enabled_user_ids), PushTokenModel.revoked_at.is_(None))
        .all()
    )
    return [row.token for row in rows]


def _recipient_users(session: Session, recipient: dict) -> list[UserModel]:
    if recipient["kind"] == "worker":
        return session.query(UserModel).filter(UserModel.worker_profile_id == recipient["id"]).all()
    if recipient["kind"] == "venue":
        return session.query(UserModel).filter(UserModel.active_venue_id == recipient["id"]).all()
    return []


def _normalized(raw: object, defaults: dict[str, bool]) -> dict[str, bool]:
    values = dict(defaults)
    if isinstance(raw, dict):
        values.update(
            {key: value for key, value in raw.items() if key in values and isinstance(value, bool)}
        )
    return values

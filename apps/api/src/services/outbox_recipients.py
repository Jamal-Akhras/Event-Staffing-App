from __future__ import annotations

from sqlalchemy.orm import Session

from apps.api.src.db.models import UserModel
from apps.api.src.db.notification_models import PushTokenModel, UserNotificationPreferenceModel
from apps.api.src.db.tenancy_models import OrganisationMembershipModel, VenueModel
from apps.api.src.services.notification_settings import CATEGORY_DEFAULTS, CHANNEL_DEFAULTS, normalize_flags


def channel_enabled(session: Session, recipient: dict, channel: str, payload: dict) -> bool:
    if payload.get("transactional"):
        return True
    users = _recipient_users(session, recipient)
    if not users:
        return channel == "in_app"
    return bool(_opted_in(session, users, channel, payload["category"]))


def push_tokens(session: Session, recipient_kind: str, recipient_id: str, payload: dict) -> list[str]:
    users = _recipient_users(session, {"kind": recipient_kind, "id": recipient_id})
    user_ids = _opted_in(session, users, "push", payload["category"])
    if not user_ids:
        return []
    rows = (
        session.query(PushTokenModel.token)
        .filter(PushTokenModel.user_id.in_(user_ids), PushTokenModel.revoked_at.is_(None))
        .all()
    )
    return [row.token for row in rows]


def _opted_in(session: Session, users: list[UserModel], channel: str, category: str) -> list[str]:
    opted_in = []
    for user in users:
        preferences = session.get(UserNotificationPreferenceModel, user.user_id)
        channels = normalize_flags(preferences.channels if preferences else None, CHANNEL_DEFAULTS)
        categories = normalize_flags(preferences.categories if preferences else None, CATEGORY_DEFAULTS)
        if channels[channel] and categories[category]:
            opted_in.append(user.user_id)
    return opted_in


def _recipient_users(session: Session, recipient: dict) -> list[UserModel]:
    if recipient["kind"] == "worker":
        return session.query(UserModel).filter(UserModel.worker_profile_id == recipient["id"]).all()
    if recipient["kind"] == "venue":
        venue = session.get(VenueModel, recipient["id"])
        if venue is None:
            return []
        memberships = (
            session.query(OrganisationMembershipModel)
            .filter(OrganisationMembershipModel.organisation_id == venue.organisation_id)
            .all()
        )
        user_ids = [
            membership.user_id
            for membership in memberships
            if membership.venue_scope is None or recipient["id"] in membership.venue_scope
        ]
        if not user_ids:
            return []
        return session.query(UserModel).filter(UserModel.user_id.in_(user_ids)).all()
    return []

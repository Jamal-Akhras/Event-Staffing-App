from __future__ import annotations

from dataclasses import replace
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from secrets import token_urlsafe
from typing import Any

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from apps.api.src.auth.password import hash_password
from apps.api.src.db.models import (
    ApplicationModel,
    BookingModel,
    MessageModel,
    NotificationModel,
    RatingModel,
    ShiftModel,
    WorkerProfileModel,
)
from apps.api.src.db.notification_models import PushTokenModel
from apps.api.src.db.trust_models import ReportModel
from apps.api.src.models.user import User
from apps.api.src.repositories.user_repository import UserRepository
from apps.api.src.repositories.worker_profile_repository import WorkerProfileRepository


def build_account_export(session: Session, user: User, generated_at: datetime) -> dict[str, Any]:
    worker_id = user.worker_profile_id
    venue_id = user.account_id
    data: dict[str, Any] = {
        "account": _values(
            user,
            "user_id",
            "email",
            "role",
            "account_id",
            "worker_profile_id",
            "is_active",
            "email_verified",
            "created_at",
            "updated_at",
        ),
        "generated_at": generated_at,
    }
    data["worker_profile"] = _model_or_none(
        session.get(WorkerProfileModel, worker_id) if worker_id else None
    )
    shifts = _shift_query(session, user)
    shift_ids = [row.shift_id for row in shifts]
    data["shifts"] = [_model(row) for row in shifts]
    data["applications"] = [_model(row) for row in _applications(session, worker_id, shift_ids)]
    data["bookings"] = [_model(row) for row in _bookings(session, worker_id, shift_ids)]
    sender_id = worker_id or user.user_id
    data["messages_sent"] = [
        _model(row)
        for row in session.scalars(
            select(MessageModel).where(MessageModel.sender_id == sender_id).order_by(MessageModel.created_at)
        )
    ]
    data["ratings_given"] = [
        _model(row)
        for row in session.scalars(
            select(RatingModel).where(RatingModel.rater_id == sender_id).order_by(RatingModel.created_at)
        )
    ]
    notification_filter = (
        NotificationModel.worker_id == worker_id
        if worker_id
        else NotificationModel.venue_id == venue_id
    )
    data["notifications"] = [
        _model(row)
        for row in session.scalars(select(NotificationModel).where(notification_filter))
    ]
    data["reports"] = [
        _model(row)
        for row in session.scalars(
            select(ReportModel).where(ReportModel.reporter_user_id == user.user_id)
        )
    ]
    data["registered_devices"] = [
        _values(row, "push_token_id", "platform", "device_id", "created_at", "updated_at", "revoked_at")
        for row in session.scalars(select(PushTokenModel).where(PushTokenModel.user_id == user.user_id))
    ]
    return _json_value(data)


def deactivate_account(
    session: Session | None,
    user_repo: UserRepository,
    worker_repo: WorkerProfileRepository,
    user: User,
    now: datetime,
) -> str | None:
    retired_avatar: str | None = None
    if user.worker_profile_id:
        profile = worker_repo.get(user.worker_profile_id)
        if profile is not None:
            retired_avatar = profile.avatar_url
            worker_repo.save(
                replace(
                    profile,
                    display_name="Deleted user",
                    role="",
                    city="",
                    bio=None,
                    languages=[],
                    email=None,
                    phone=None,
                    address=None,
                    emergency_contact=None,
                    pay_rate=None,
                    notes=None,
                    allow_venue_recontact=False,
                    avatar_url=None,
                    market_id=None,
                    updated_at=now,
                )
            )
    user_repo.save(
        replace(
            user,
            email=f"deleted+{user.user_id}@deleted.invalid",
            hashed_password=hash_password(token_urlsafe(48)),
            is_active=False,
            updated_at=now,
            email_verified=False,
            email_verification_token=None,
            session_version=user.session_version + 1,
            deactivated_at=now,
            anonymized_at=now,
        )
    )
    if session is not None:
        session.execute(
            update(PushTokenModel)
            .where(PushTokenModel.user_id == user.user_id)
            .values(revoked_at=now, updated_at=now)
        )
    return retired_avatar


def _shift_query(session: Session, user: User) -> list[ShiftModel]:
    if user.account_id:
        return list(session.scalars(select(ShiftModel).where(ShiftModel.venue_id == user.account_id)))
    if not user.worker_profile_id:
        return []
    return list(
        session.scalars(
            select(ShiftModel)
            .join(BookingModel, BookingModel.shift_id == ShiftModel.shift_id)
            .where(BookingModel.worker_id == user.worker_profile_id)
            .distinct()
        )
    )


def _applications(session: Session, worker_id: str | None, shift_ids: list[str]) -> list[ApplicationModel]:
    if worker_id:
        return list(session.scalars(select(ApplicationModel).where(ApplicationModel.worker_id == worker_id)))
    if not shift_ids:
        return []
    return list(session.scalars(select(ApplicationModel).where(ApplicationModel.shift_id.in_(shift_ids))))


def _bookings(session: Session, worker_id: str | None, shift_ids: list[str]) -> list[BookingModel]:
    if worker_id:
        return list(session.scalars(select(BookingModel).where(BookingModel.worker_id == worker_id)))
    if not shift_ids:
        return []
    return list(session.scalars(select(BookingModel).where(BookingModel.shift_id.in_(shift_ids))))


def _model_or_none(row: object | None) -> dict[str, Any] | None:
    return _model(row) if row is not None else None


def _model(row: object) -> dict[str, Any]:
    return {
        column.name: _json_value(getattr(row, column.name))
        for column in row.__table__.columns
        if column.name not in {"hashed_password", "email_verification_token", "token"}
    }


def _values(row: object, *fields: str) -> dict[str, Any]:
    return {field: _json_value(getattr(row, field)) for field in fields}


def _json_value(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: _json_value(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_json_value(item) for item in value]
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, Enum):
        return value.value
    return value

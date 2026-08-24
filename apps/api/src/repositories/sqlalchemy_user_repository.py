from __future__ import annotations

from sqlalchemy.orm import Session
from sqlalchemy import select

from apps.api.src.db.models import UserModel
from apps.api.src.models.user import User


class SqlAlchemyUserRepository:
    """SQLAlchemy implementation of UserRepository."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def get(self, user_id: str) -> User | None:
        """Get a user by ID."""
        model = self._session.get(UserModel, user_id)
        if model is None:
            return None
        return _to_domain(model)

    def get_by_email(self, email: str) -> User | None:
        """Get a user by email address."""
        stmt = select(UserModel).where(UserModel.email == email)
        model = self._session.execute(stmt).scalar_one_or_none()
        if model is None:
            return None
        return _to_domain(model)

    def get_by_verification_token(self, token: str) -> User | None:
        stmt = select(UserModel).where(UserModel.email_verification_token == token)
        model = self._session.execute(stmt).scalar_one_or_none()
        if model is None:
            return None
        return _to_domain(model)

    def save(self, user: User) -> User:
        """Save a user (create or update)."""
        model = self._session.get(UserModel, user.user_id)
        if model is None:
            model = UserModel(user_id=user.user_id)
            self._session.add(model)
        _apply_domain(model, user)
        self._session.flush()
        return user


def _to_domain(model: UserModel) -> User:
    """Convert SQLAlchemy model to domain model."""
    return User(
        user_id=model.user_id,
        email=model.email,
        hashed_password=model.hashed_password,
        role=model.role,
        account_id=getattr(model, "account_id", None),
        worker_profile_id=model.worker_profile_id,
        is_active=model.is_active,
        created_at=model.created_at,
        updated_at=model.updated_at,
        password_changed_at=getattr(model, "password_changed_at", None),
        email_verified=bool(getattr(model, "email_verified", False)),
        email_verification_token=getattr(model, "email_verification_token", None),
        session_version=int(getattr(model, "session_version", 0)),
        deactivated_at=getattr(model, "deactivated_at", None),
        anonymized_at=getattr(model, "anonymized_at", None),
    )


def _apply_domain(model: UserModel, user: User) -> None:
    """Apply domain model fields to SQLAlchemy model."""
    model.email = user.email
    model.hashed_password = user.hashed_password
    model.role = user.role
    model.account_id = user.account_id
    model.worker_profile_id = user.worker_profile_id
    model.is_active = user.is_active
    model.created_at = user.created_at
    model.updated_at = user.updated_at
    if hasattr(model, "password_changed_at"):
        model.password_changed_at = user.password_changed_at
    if hasattr(model, "email_verified"):
        model.email_verified = user.email_verified
    if hasattr(model, "email_verification_token"):
        model.email_verification_token = user.email_verification_token
    if hasattr(model, "session_version"):
        model.session_version = user.session_version
    if hasattr(model, "deactivated_at"):
        model.deactivated_at = user.deactivated_at
    if hasattr(model, "anonymized_at"):
        model.anonymized_at = user.anonymized_at

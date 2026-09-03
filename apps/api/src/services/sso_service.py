from __future__ import annotations

import secrets
from dataclasses import replace
from datetime import datetime
from uuid import uuid4

from apps.api.src.auth.password import hash_password
from apps.api.src.models.user import User
from apps.api.src.models.worker_profile import WorkerProfile
from apps.api.src.repositories.user_repository import UserRepository
from apps.api.src.repositories.worker_profile_repository import WorkerProfileRepository
from apps.api.src.services.clerk_identity import SsoIdentity


class SsoRegistrationRequired(Exception):
    def __init__(self, email: str) -> None:
        super().__init__("No account exists for this email; registration is required.")
        self.email = email


class SsoEmailUnverified(Exception):
    pass


class SsoAccountInactive(Exception):
    pass


def unusable_password_hash() -> str:
    return hash_password(secrets.token_urlsafe(32))


class SsoService:
    def __init__(self, user_repo: UserRepository, worker_repo: WorkerProfileRepository) -> None:
        self._users = user_repo
        self._workers = worker_repo

    def sign_in(self, identity: SsoIdentity, role: str, now: datetime) -> User:
        if not identity.email_verified:
            raise SsoEmailUnverified()
        user = self._users.get_by_sso_subject(identity.provider, identity.subject)
        if user is None:
            user = self._link_existing(identity, now)
        if user is None:
            if role != "worker":
                raise SsoRegistrationRequired(identity.email)
            user = self._create_worker(identity, now)
        if not user.is_active:
            raise SsoAccountInactive()
        return user

    def _link_existing(self, identity: SsoIdentity, now: datetime) -> User | None:
        user = self._users.get_by_email(identity.email)
        if user is None:
            return None
        linked = replace(
            user,
            sso_provider=identity.provider,
            sso_subject=identity.subject,
            email_verified=True,
            email_verification_token=None,
            updated_at=now,
        )
        return self._users.save(linked)

    def _create_worker(self, identity: SsoIdentity, now: datetime) -> User:
        worker_profile_id = str(uuid4())
        user = User(
            user_id=str(uuid4()),
            email=identity.email,
            hashed_password=unusable_password_hash(),
            role="worker",
            account_id=None,
            worker_profile_id=worker_profile_id,
            is_active=True,
            created_at=now,
            updated_at=now,
            email_verified=True,
            email_verification_token=None,
            sso_provider=identity.provider,
            sso_subject=identity.subject,
        )
        self._users.save(user)
        self._workers.save(
            WorkerProfile(
                worker_id=worker_profile_id,
                display_name=identity.display_name or "",
                role="",
                city="",
                experience_years=0,
                reliability_score=0.0,
                badges=[],
                bio=None,
                languages=[],
                email=identity.email,
                phone=None,
                address=None,
                emergency_contact=None,
                pay_rate=None,
                notes=None,
                updated_at=now,
                marketplace_enabled=True,
            )
        )
        return user

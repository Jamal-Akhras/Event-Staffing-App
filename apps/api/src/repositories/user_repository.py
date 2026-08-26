from __future__ import annotations

from typing import Protocol

from apps.api.src.models.user import User


class UserRepository(Protocol):
    def get(self, user_id: str) -> User | None:
        ...

    def get_by_email(self, email: str) -> User | None:
        ...

    def get_by_verification_token(self, token: str) -> User | None:
        ...

    def get_by_sso_subject(self, provider: str, subject: str) -> User | None:
        ...

    def save(self, user: User) -> User:
        ...

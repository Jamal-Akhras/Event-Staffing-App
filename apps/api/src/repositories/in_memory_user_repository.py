from __future__ import annotations

from typing import Dict

from apps.api.src.models.user import User


class InMemoryUserRepository:
    def __init__(self) -> None:
        self._users: Dict[str, User] = {}
        self._users_by_email: Dict[str, User] = {}

    def get(self, user_id: str) -> User | None:
        return self._users.get(user_id)

    def get_by_email(self, email: str) -> User | None:
        return self._users_by_email.get(email.lower())

    def get_by_verification_token(self, token: str) -> User | None:
        for user in self._users.values():
            if user.email_verification_token == token:
                return user
        return None

    def get_by_sso_subject(self, provider: str, subject: str) -> User | None:
        for user in self._users.values():
            if user.sso_provider == provider and user.sso_subject == subject:
                return user
        return None

    def save(self, user: User) -> User:
        previous = self._users.get(user.user_id)
        if previous is not None and previous.email.lower() != user.email.lower():
            self._users_by_email.pop(previous.email.lower(), None)
        self._users[user.user_id] = user
        self._users_by_email[user.email.lower()] = user
        return user

    def clear(self) -> None:
        self._users.clear()
        self._users_by_email.clear()

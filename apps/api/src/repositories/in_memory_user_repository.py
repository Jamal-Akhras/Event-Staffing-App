from __future__ import annotations

from typing import Dict

from apps.api.src.models.user import User


class InMemoryUserRepository:
    """In-memory implementation of UserRepository for testing."""

    def __init__(self) -> None:
        self._users: Dict[str, User] = {}
        self._users_by_email: Dict[str, User] = {}

    def get(self, user_id: str) -> User | None:
        """Get a user by ID."""
        return self._users.get(user_id)

    def get_by_email(self, email: str) -> User | None:
        """Get a user by email address."""
        return self._users_by_email.get(email.lower())

    def save(self, user: User) -> User:
        """Save a user (create or update)."""
        self._users[user.user_id] = user
        self._users_by_email[user.email.lower()] = user
        return user

    def clear(self) -> None:
        """Clear all users (for testing)."""
        self._users.clear()
        self._users_by_email.clear()

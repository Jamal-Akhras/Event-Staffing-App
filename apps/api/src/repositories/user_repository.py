from __future__ import annotations

from typing import Protocol

from apps.api.src.models.user import User


class UserRepository(Protocol):
    """Repository interface for User domain model."""

    def get(self, user_id: str) -> User | None:
        """Get a user by ID.

        Args:
            user_id: The user's unique identifier

        Returns:
            User if found, None otherwise
        """
        raise NotImplementedError

    def get_by_email(self, email: str) -> User | None:
        """Get a user by email address.

        Args:
            email: The user's email address

        Returns:
            User if found, None otherwise
        """
        raise NotImplementedError

    def save(self, user: User) -> User:
        """Save a user (create or update).

        Args:
            user: The user to save

        Returns:
            The saved user
        """
        raise NotImplementedError

#!/usr/bin/env python
"""Script to create an operator account.

Usage:
    python -m apps.api.scripts.create_operator <email> <password>

Example:
    python -m apps.api.scripts.create_operator admin@example.com SecurePass123
"""

import sys
from datetime import datetime
from uuid import uuid4

from apps.api.src.auth.password import hash_password
from apps.api.src.db.database import SessionLocal
from apps.api.src.models.user import User
from apps.api.src.repositories.sqlalchemy_user_repository import SqlAlchemyUserRepository


def create_operator(email: str, password: str) -> None:
    """Create an operator account.

    Args:
        email: Email address for the operator account
        password: Plain text password (will be hashed)
    """
    session = SessionLocal()
    try:
        repo = SqlAlchemyUserRepository(session)

        # Check if user already exists
        existing = repo.get_by_email(email)
        if existing:
            print(f"Error: User with email '{email}' already exists")
            sys.exit(1)

        # Create operator user
        now = datetime.utcnow()
        user = User(
            user_id=str(uuid4()),
            email=email,
            hashed_password=hash_password(password),
            role="operator",
            worker_profile_id=None,
            is_active=True,
            created_at=now,
            updated_at=now,
        )

        repo.save(user)
        print(f"✓ Created operator account: {email}")
        print(f"  User ID: {user.user_id}")
        print(f"  Role: {user.role}")

    finally:
        session.close()


def main() -> None:
    """Main entry point for the script."""
    if len(sys.argv) != 3:
        print("Usage: python -m apps.api.scripts.create_operator <email> <password>")
        print()
        print("Example:")
        print("  python -m apps.api.scripts.create_operator admin@example.com SecurePass123")
        sys.exit(1)

    email = sys.argv[1]
    password = sys.argv[2]

    if not email or "@" not in email:
        print("Error: Invalid email address")
        sys.exit(1)

    if len(password) < 8:
        print("Error: Password must be at least 8 characters long")
        sys.exit(1)

    create_operator(email, password)


if __name__ == "__main__":
    main()

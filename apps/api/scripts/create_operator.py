#!/usr/bin/env python
"""Script to create an operator account.

Usage:
    python -m apps.api.scripts.create_operator <email> <password> <venue_name> <market_id>

Example:
    python -m apps.api.scripts.create_operator admin@example.com SecurePass123 "Bath Venue" bath-gb
"""

import sys
from uuid import uuid4

from apps.api.src.auth.password import hash_password
from apps.api.src.db.database import SessionLocal
from apps.api.src.datetime_utils import utc_now
from apps.api.src.models.user import User
from apps.api.src.models.organisation import (
    Organisation,
    OrganisationMembership,
    OrganisationRole,
    Venue,
)
from apps.api.src.repositories.sqlalchemy_organisation_repository import SqlAlchemyOrganisationRepository
from apps.api.src.repositories.sqlalchemy_market_repository import SqlAlchemyMarketRepository
from apps.api.src.repositories.sqlalchemy_user_repository import SqlAlchemyUserRepository


def create_operator(email: str, password: str, venue_name: str, market_id: str) -> None:
    """Create an operator account.

    Args:
        email: Email address for the operator account
        password: Plain text password (will be hashed)
    """
    session = SessionLocal()
    try:
        repo = SqlAlchemyUserRepository(session)
        organisation_repo = SqlAlchemyOrganisationRepository(session)
        market_repo = SqlAlchemyMarketRepository(session)

        # Check if user already exists
        existing = repo.get_by_email(email)
        if existing:
            print(f"Error: User with email '{email}' already exists")
            sys.exit(1)

        market = market_repo.get(market_id)
        if market is None or not market.is_active:
            raise ValueError(f"Unknown or inactive market: {market_id}")

        # Create operator user
        now = utc_now()
        organisation_id = str(uuid4())
        venue_id = str(uuid4())
        user_id = str(uuid4())
        organisation_repo.save_organisation(
            Organisation(organisation_id, venue_name, market.country, market.currency, now)
        )
        organisation_repo.save_venue(
            Venue(
                venue_id,
                organisation_id,
                venue_name,
                market.country,
                market.currency,
                now,
                market_id=market.market_id,
            )
        )
        user = User(
            user_id=user_id,
            email=email,
            hashed_password=hash_password(password),
            role="operator",
            account_id=venue_id,
            worker_profile_id=None,
            is_active=True,
            created_at=now,
            updated_at=now,
        )

        repo.save(user)
        organisation_repo.save_membership(
            OrganisationMembership(organisation_id, user_id, OrganisationRole.OWNER, now)
        )
        session.commit()
        print(f"✓ Created operator account: {email}")
        print(f"  User ID: {user.user_id}")
        print(f"  Role: {user.role}")

    except BaseException:
        session.rollback()
        raise
    finally:
        session.close()


def main() -> None:
    """Main entry point for the script."""
    if len(sys.argv) != 5:
        print("Usage: python -m apps.api.scripts.create_operator <email> <password> <venue_name> <market_id>")
        print()
        print("Example:")
        print('  python -m apps.api.scripts.create_operator admin@example.com SecurePass123 "Bath Venue" bath-gb')
        sys.exit(1)

    email = sys.argv[1]
    password = sys.argv[2]
    venue_name = sys.argv[3].strip()
    market_id = sys.argv[4].strip()

    if not email or "@" not in email:
        print("Error: Invalid email address")
        sys.exit(1)

    if len(password) < 8:
        print("Error: Password must be at least 8 characters long")
        sys.exit(1)

    if not venue_name:
        print("Error: Venue name is required")
        sys.exit(1)

    if not market_id:
        print("Error: Market ID is required")
        sys.exit(1)

    create_operator(email, password, venue_name, market_id)


if __name__ == "__main__":
    main()

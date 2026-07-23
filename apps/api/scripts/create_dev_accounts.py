"""Create dev/test operator accounts in the database."""
from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from apps.api.src.auth.password import hash_password
from apps.api.src.db.database import Base, SessionLocal, engine
from apps.api.src.db.models import AccountModel, UserModel

import os

# Local development seed accounts only. Addresses are RFC 2606 reserved
# example domains; the password is dev-only and overridable via env.
DEV_PASSWORD = os.environ.get("DEV_ACCOUNT_PASSWORD", "change-me-dev-only")

ACCOUNTS = [
    {
        "email": "operator-one@example.com",
        "password": DEV_PASSWORD,
        "venue_name": "Riverside Hall",
        "country": "GB",
        "currency": "GBP",
    },
    {
        "email": "operator-two@example.com",
        "password": DEV_PASSWORD,
        "venue_name": "The Warehouse",
        "country": "GB",
        "currency": "GBP",
    },
]


def main() -> None:
    Base.metadata.create_all(bind=engine)
    now = datetime.utcnow()

    with SessionLocal() as session:
        for spec in ACCOUNTS:
            # Check if user already exists
            existing = session.query(UserModel).filter_by(email=spec["email"]).first()
            if existing:
                print(f"  SKIP  {spec['email']} — already exists (user_id={existing.user_id})")
                continue

            account_id = str(uuid4())
            user_id = str(uuid4())

            session.add(AccountModel(
                account_id=account_id,
                name=spec["venue_name"],
                country=spec["country"],
                currency=spec["currency"],
                created_at=now,
            ))

            session.add(UserModel(
                user_id=user_id,
                email=spec["email"],
                hashed_password=hash_password(spec["password"]),
                role="operator",
                account_id=account_id,
                worker_profile_id=None,
                is_active=True,
                created_at=now,
                updated_at=now,
            ))

            session.commit()
            print(f"  OK    {spec['email']} — user_id={user_id}  account_id={account_id}")

    print("Done.")


if __name__ == "__main__":
    main()

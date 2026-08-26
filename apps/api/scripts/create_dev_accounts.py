from __future__ import annotations

from uuid import uuid4

from apps.api.src.auth.password import hash_password
from apps.api.src.db.database import Base, SessionLocal, engine
from apps.api.src.db.models import (
    OrganisationMembershipModel,
    OrganisationModel,
    MarketModel,
    UserModel,
    VenueModel,
)
from apps.api.src.datetime_utils import utc_now

import os


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
    now = utc_now()

    with SessionLocal() as session:
        market = session.get(MarketModel, "bath-gb")
        if market is None:
            market = MarketModel(
                market_id="bath-gb",
                name="Bath",
                country="GB",
                currency="GBP",
                timezone="Europe/London",
                high_pay_threshold=15,
                is_active=True,
                created_at=now,
            )
            session.add(market)
        for spec in ACCOUNTS:
            existing = session.query(UserModel).filter_by(email=spec["email"]).first()
            if existing:
                print(f"  SKIP  {spec['email']} — already exists (user_id={existing.user_id})")
                continue

            organisation_id = str(uuid4())
            venue_id = str(uuid4())
            user_id = str(uuid4())

            session.add(OrganisationModel(
                organisation_id=organisation_id,
                market_id=market.market_id,
                name=spec["venue_name"],
                country=spec["country"],
                currency=spec["currency"],
                created_at=now,
            ))
            session.add(VenueModel(
                venue_id=venue_id,
                organisation_id=organisation_id,
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
                account_id=venue_id,
                worker_profile_id=None,
                is_active=True,
                created_at=now,
                updated_at=now,
            ))
            session.add(OrganisationMembershipModel(
                organisation_id=organisation_id,
                user_id=user_id,
                role="owner",
                created_at=now,
            ))

            session.commit()
            print(f"  OK    {spec['email']} — user_id={user_id}  venue_id={venue_id}")

    print("Done.")


if __name__ == "__main__":
    main()

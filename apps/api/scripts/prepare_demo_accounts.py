from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy.orm import Session

from apps.api.src.auth.password import hash_password
from apps.api.src.config import get_env
from apps.api.src.db.database import SessionLocal
from apps.api.src.db.models import (
    AccountModel,
    MarketModel,
    OrganisationMembershipModel,
    OrganisationModel,
    UserModel,
    WorkerProfileModel,
)


VENUE_ACCOUNT_ID = "demo-venue-account"
ORGANISATION_ID = "demo-venue-organisation"
VENUE_USER_ID = "demo-venue-user"
WORKER_PROFILE_ID = "demo-worker-profile"
WORKER_USER_ID = "demo-worker-user"


def prepare_demo_accounts(
    session: Session,
    venue_email: str,
    worker_email: str,
    password: str,
    now: datetime,
) -> tuple[UserModel, UserModel]:
    if len(password) < 8:
        raise ValueError("DEMO_ACCOUNT_PASSWORD must contain at least 8 characters.")

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

    organisation = session.get(OrganisationModel, ORGANISATION_ID)
    if organisation is None:
        organisation = OrganisationModel(organisation_id=ORGANISATION_ID, created_at=now)
        session.add(organisation)
    organisation.name = "Temp Venue"
    organisation.country = "GB"
    organisation.currency = "GBP"

    account = session.get(AccountModel, VENUE_ACCOUNT_ID)
    if account is None:
        account = AccountModel(
            account_id=VENUE_ACCOUNT_ID,
            organisation_id=ORGANISATION_ID,
            created_at=now,
        )
        session.add(account)
    account.organisation_id = ORGANISATION_ID
    account.market_id = market.market_id
    account.name = "Temp Venue"
    account.country = "GB"
    account.currency = "GBP"
    account.venue_type = "Hospitality"
    account.default_location = "Bath"

    worker_profile = session.get(WorkerProfileModel, WORKER_PROFILE_ID)
    if worker_profile is None:
        worker_profile = WorkerProfileModel(worker_id=WORKER_PROFILE_ID)
        session.add(worker_profile)
    worker_profile.display_name = "Temp Worker"
    worker_profile.role = "Bartender"
    worker_profile.city = "Bath"
    worker_profile.experience_years = 0
    worker_profile.reliability_score = 0.0
    worker_profile.badges = ["New worker"]
    worker_profile.bio = "Available for hospitality shifts in Bath."
    worker_profile.languages = ["English"]
    worker_profile.email = worker_email
    worker_profile.updated_at = now
    worker_profile.allow_venue_recontact = True
    worker_profile.market_id = market.market_id
    session.flush()

    password_hash = hash_password(password)
    venue_user = _upsert_user(
        session=session,
        preferred_id=VENUE_USER_ID,
        email=venue_email,
        password_hash=password_hash,
        role="operator",
        account_id=VENUE_ACCOUNT_ID,
        worker_profile_id=None,
        now=now,
    )
    worker_user = _upsert_user(
        session=session,
        preferred_id=WORKER_USER_ID,
        email=worker_email,
        password_hash=password_hash,
        role="worker",
        account_id=None,
        worker_profile_id=WORKER_PROFILE_ID,
        now=now,
    )
    membership = session.get(
        OrganisationMembershipModel,
        (ORGANISATION_ID, venue_user.user_id),
    )
    if membership is None:
        membership = OrganisationMembershipModel(
            organisation_id=ORGANISATION_ID,
            user_id=venue_user.user_id,
        )
        session.add(membership)
    membership.role = "owner"
    membership.created_at = now
    session.flush()
    return venue_user, worker_user


def _upsert_user(
    session: Session,
    preferred_id: str,
    email: str,
    password_hash: str,
    role: str,
    account_id: str | None,
    worker_profile_id: str | None,
    now: datetime,
) -> UserModel:
    user = session.query(UserModel).filter(UserModel.email == email).one_or_none()
    if user is None:
        user = UserModel(user_id=preferred_id, created_at=now)
        session.add(user)
    user.email = email
    user.hashed_password = password_hash
    user.role = role
    user.account_id = account_id
    user.worker_profile_id = worker_profile_id
    user.is_active = True
    user.updated_at = now
    user.password_changed_at = now
    user.email_verified = True
    user.email_verification_token = None
    return user


def main() -> None:
    venue_email = get_env("DEMO_VENUE_EMAIL", "venue@temp.com").strip().lower()
    worker_email = get_env("DEMO_WORKER_EMAIL", "user@temp.com").strip().lower()
    password = get_env("DEMO_ACCOUNT_PASSWORD")
    if not password:
        raise RuntimeError("Set DEMO_ACCOUNT_PASSWORD before preparing demo accounts.")

    now = datetime.now(UTC).replace(microsecond=0)
    with SessionLocal() as session:
        prepare_demo_accounts(session, venue_email, worker_email, password, now)
        session.commit()

    print(f"Venue login: {venue_email}")
    print(f"Worker login: {worker_email}")
    print("Demo accounts are active, verified, and ready to use.")


if __name__ == "__main__":
    main()

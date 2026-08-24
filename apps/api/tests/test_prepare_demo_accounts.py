from datetime import UTC, datetime

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from apps.api.scripts.prepare_demo_accounts import (
    VENUE_ACCOUNT_ID,
    WORKER_PROFILE_ID,
    prepare_demo_accounts,
)
from apps.api.src.auth.password import verify_password
from apps.api.src.db.database import Base
from apps.api.src.db.models import AccountModel, UserModel, WorkerProfileModel


def test_prepare_demo_accounts_is_complete_and_idempotent():
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine)
    now = datetime.now(UTC)

    with session_factory() as session:
        prepare_demo_accounts(
            session,
            "venue@temp.com",
            "user@temp.com",
            "Temp123!",
            now,
        )
        session.commit()
        prepare_demo_accounts(
            session,
            "venue@temp.com",
            "user@temp.com",
            "Temp123!",
            now,
        )
        session.commit()

        venue_user = session.query(UserModel).filter_by(email="venue@temp.com").one()
        worker_user = session.query(UserModel).filter_by(email="user@temp.com").one()
        account = session.get(AccountModel, VENUE_ACCOUNT_ID)
        worker_profile = session.get(WorkerProfileModel, WORKER_PROFILE_ID)

        assert session.query(UserModel).count() == 2
        assert venue_user.role == "operator"
        assert venue_user.account_id == VENUE_ACCOUNT_ID
        assert venue_user.email_verified is True
        assert verify_password("Temp123!", venue_user.hashed_password)
        assert account is not None
        assert account.name == "Temp Venue"
        assert account.default_location == "Bath"

        assert worker_user.role == "worker"
        assert worker_user.worker_profile_id == WORKER_PROFILE_ID
        assert worker_user.email_verified is True
        assert verify_password("Temp123!", worker_user.hashed_password)
        assert worker_profile is not None
        assert worker_profile.city == "Bath"

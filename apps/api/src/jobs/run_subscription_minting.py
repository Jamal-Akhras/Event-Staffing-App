from __future__ import annotations

from datetime import datetime

from apps.api.src.datetime_utils import utc_now
from apps.api.src.db.database import SessionLocal
from apps.api.src.db.tenancy_models import OrganisationModel
from apps.api.src.repositories.sqlalchemy_commercial_repository import (
    SqlAlchemyCommercialAgreementRepository,
    SqlAlchemyShiftBoostRepository,
    SqlAlchemySubscriptionChargeRepository,
)
from apps.api.src.repositories.sqlalchemy_organisation_repository import (
    SqlAlchemyOrganisationRepository,
)
from apps.api.src.repositories.sqlalchemy_shift_repository import SqlAlchemyShiftRepository
from apps.api.src.services.commercial_service import CommercialService


def run(now: datetime | None = None, period: str | None = None) -> int:
    moment = now or utc_now()
    target_period = period or moment.strftime("%Y-%m")
    with SessionLocal() as session, session.begin():
        service = CommercialService(
            SqlAlchemyCommercialAgreementRepository(session),
            SqlAlchemySubscriptionChargeRepository(session),
            SqlAlchemyShiftBoostRepository(session),
            SqlAlchemyOrganisationRepository(session),
            SqlAlchemyShiftRepository(session),
        )
        minted = 0
        for organisation_id in session.query(OrganisationModel.organisation_id).all():
            minted += service.mint_subscriptions(organisation_id[0], target_period, moment)
        return minted


if __name__ == "__main__":
    print(f"Subscription minting created {run()} charge(s).")

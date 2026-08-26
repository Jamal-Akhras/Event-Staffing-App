from __future__ import annotations

import threading
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest
from sqlalchemy import func, select

from apps.api.src.db.billing_models import PartnerCodeRedemptionModel
from apps.api.src.db.tenancy_models import OrganisationModel, VenueModel
from apps.api.src.models.partner_code import PartnerCode
from apps.api.src.repositories.sqlalchemy_booking_repository import SqlAlchemyBookingRepository
from apps.api.src.repositories.sqlalchemy_partner_code_repository import SqlAlchemyPartnerCodeRepository
from apps.api.src.repositories.sqlalchemy_shift_repository import SqlAlchemyShiftRepository
from apps.api.src.repositories.sqlalchemy_worker_profile_repository import SqlAlchemyWorkerProfileRepository
from apps.api.src.services.billing_service import BillingService
from apps.api.src.services.errors import ConflictError

pytestmark = pytest.mark.postgres

NOW = datetime(2030, 1, 1, tzinfo=UTC)


def _seed() -> None:
    from apps.api.src.db.database import SessionLocal

    with SessionLocal() as session, session.begin():
        for index in range(2):
            organisation_id = f"organisation-{index}"
            session.add(
                OrganisationModel(
                    organisation_id=organisation_id,
                    name=f"Organisation {index}",
                    country="GB",
                    currency="GBP",
                    created_at=NOW,
                )
            )
            session.add(
                VenueModel(
                    venue_id=f"venue-{index}",
                    organisation_id=organisation_id,
                    market_id="bath-gb",
                    name=f"Venue {index}",
                    country="GB",
                    currency="GBP",
                    created_at=NOW,
                )
            )
        SqlAlchemyPartnerCodeRepository(session).save_code(
            PartnerCode(
                code="BATH-RACE-CODE",
                label="Concurrency test",
                waiver_months=3,
                shift_cap=20,
                max_redemptions=1,
                created_at=NOW,
                created_by="test",
                expires_at=NOW + timedelta(days=30),
            )
        )


def test_partner_code_redemption_limit_is_atomic() -> None:
    from apps.api.src.db.database import SessionLocal

    _seed()
    barrier = threading.Barrier(2)
    outcomes: list[str] = []
    errors: list[BaseException] = []
    result_lock = threading.Lock()

    def redeem(index: int) -> None:
        try:
            with SessionLocal() as session, session.begin():
                barrier.wait(timeout=10)
                service = BillingService(
                    SqlAlchemyBookingRepository(session),
                    SqlAlchemyShiftRepository(session),
                    SqlAlchemyWorkerProfileRepository(session),
                    SqlAlchemyPartnerCodeRepository(session),
                    Decimal("8"),
                )
                service.redeem("BATH-RACE-CODE", f"venue-{index}", f"user-{index}", NOW)
            outcome = "redeemed"
        except ConflictError:
            outcome = "refused"
        except BaseException as exc:
            with result_lock:
                errors.append(exc)
            return
        with result_lock:
            outcomes.append(outcome)

    threads = [threading.Thread(target=redeem, args=(index,)) for index in range(2)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=30)

    assert all(not thread.is_alive() for thread in threads), "redemption threads deadlocked"
    assert errors == []
    assert sorted(outcomes) == ["redeemed", "refused"]
    with SessionLocal() as session:
        count = session.scalar(select(func.count()).select_from(PartnerCodeRedemptionModel))
        assert count == 1

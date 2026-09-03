from __future__ import annotations

from datetime import datetime

from apps.api.src.datetime_utils import utc_now
from apps.api.src.db.database import SessionLocal
from apps.api.src.repositories.sqlalchemy_account_repository import SqlAlchemyAccountRepository
from apps.api.src.repositories.sqlalchemy_shift_offer_repository import (
    SqlAlchemyShiftOfferRepository,
)
from apps.api.src.repositories.sqlalchemy_shift_repository import SqlAlchemyShiftRepository
from apps.api.src.repositories.sqlalchemy_worker_relationship_repository import (
    SqlAlchemyWorkerRelationshipRepository,
)
from apps.api.src.services.escalation_service import EscalationService
from apps.api.src.services.outbox_publisher import SqlAlchemyOutboxPublisher


def run(now: datetime | None = None) -> int:
    with SessionLocal() as session, session.begin():
        service = EscalationService(
            SqlAlchemyShiftRepository(session),
            SqlAlchemyWorkerRelationshipRepository(session),
            SqlAlchemyAccountRepository(session),
            SqlAlchemyOutboxPublisher(session),
            offers=SqlAlchemyShiftOfferRepository(session),
        )
        return len(service.sweep(now or utc_now()))


if __name__ == "__main__":
    print(f"Escalation sweep moved {run()} shift(s).")

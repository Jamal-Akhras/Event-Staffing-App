from __future__ import annotations

from datetime import datetime

from apps.api.src.db.database import SessionLocal
from apps.api.src.datetime_utils import utc_now
from apps.api.src.repositories.sqlalchemy_booking_repository import SqlAlchemyBookingRepository
from apps.api.src.repositories.sqlalchemy_booking_transition_repository import SqlAlchemyBookingTransitionRepository
from apps.api.src.repositories.sqlalchemy_shift_repository import SqlAlchemyShiftRepository
from apps.api.src.repositories.sqlalchemy_worker_profile_repository import SqlAlchemyWorkerProfileRepository
from apps.api.src.schemas import BookingTransitionRequest
from apps.api.src.repositories.sqlalchemy_account_repository import SqlAlchemyAccountRepository
from apps.api.src.repositories.sqlalchemy_worker_relationship_repository import (
    SqlAlchemyWorkerRelationshipRepository,
)
from apps.api.src.services.booking_lifecycle_service import BookingLifecycleService
from apps.api.src.services.escalation_service import EscalationService
from apps.api.src.services.outbox_publisher import SqlAlchemyOutboxPublisher


def run(now: datetime | None = None) -> int:
    with SessionLocal() as session, session.begin():
        service = BookingLifecycleService(
            SqlAlchemyBookingRepository(session),
            SqlAlchemyWorkerProfileRepository(session),
            SqlAlchemyShiftRepository(session),
            SqlAlchemyOutboxPublisher(session),
            SqlAlchemyBookingTransitionRepository(session),
            EscalationService(
                SqlAlchemyShiftRepository(session),
                SqlAlchemyWorkerRelationshipRepository(session),
                SqlAlchemyAccountRepository(session),
                SqlAlchemyOutboxPublisher(session),
            ),
        )
        return len(service.sweep_no_shows(BookingTransitionRequest(now=now or utc_now())))


if __name__ == "__main__":
    print(f"No-show sweep updated {run()} bookings.")

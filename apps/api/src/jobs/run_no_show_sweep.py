from __future__ import annotations

from datetime import datetime

from apps.api.src.db.database import SessionLocal
from apps.api.src.datetime_utils import utc_now
from apps.api.src.repositories.sqlalchemy_booking_repository import (
    SqlAlchemyBookingRepository,
)
from apps.api.src.repositories.sqlalchemy_shift_repository import (
    SqlAlchemyShiftRepository,
)
from apps.api.src.repositories.sqlalchemy_worker_profile_repository import (
    SqlAlchemyWorkerProfileRepository,
)
from apps.api.src.schemas import BookingTransitionRequest
from apps.api.src.services.booking_lifecycle_service import BookingLifecycleService
from apps.api.src.services.outbox_publisher import SqlAlchemyOutboxPublisher


def run(now: datetime | None = None) -> int:
    session = SessionLocal()
    try:
        booking_repo = SqlAlchemyBookingRepository(session)
        worker_repo = SqlAlchemyWorkerProfileRepository(session)
        shift_repo = SqlAlchemyShiftRepository(session)
        service = BookingLifecycleService(
            booking_repo,
            worker_repo,
            shift_repo,
            SqlAlchemyOutboxPublisher(session),
        )
        updated = service.sweep_no_shows(BookingTransitionRequest(now=now or utc_now()))
        session.commit()
        return len(updated)
    except BaseException:
        session.rollback()
        raise
    finally:
        session.close()


if __name__ == "__main__":
    count = run()
    print(f"No-show sweep updated {count} bookings.")

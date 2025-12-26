from __future__ import annotations

from datetime import datetime

from apps.api.src.db.database import SessionLocal
from apps.api.src.repositories.sqlalchemy_booking_repository import (
    SqlAlchemyBookingRepository,
)
from apps.api.src.repositories.sqlalchemy_worker_profile_repository import (
    SqlAlchemyWorkerProfileRepository,
)
from apps.api.src.services.booking_ops import sweep_no_shows


def run(now: datetime | None = None) -> int:
    session = SessionLocal()
    try:
        booking_repo = SqlAlchemyBookingRepository(session)
        worker_repo = SqlAlchemyWorkerProfileRepository(session)
        updated = sweep_no_shows(booking_repo, worker_repo, now or datetime.utcnow())
        return len(updated)
    finally:
        session.close()


if __name__ == "__main__":
    count = run()
    print(f"No-show sweep updated {count} bookings.")

from __future__ import annotations

from datetime import datetime

from apps.api.src.datetime_utils import utc_now
from apps.api.src.db.database import SessionLocal
from apps.api.src.repositories.sqlalchemy_booking_repository import SqlAlchemyBookingRepository
from apps.api.src.repositories.sqlalchemy_shift_change_request_repository import (
    SqlAlchemyShiftChangeRequestRepository,
    SqlAlchemyShiftChangeTransitionRepository,
)
from apps.api.src.services.shift_change_service import expire_change_requests


def run(now: datetime | None = None) -> int:
    with SessionLocal() as session, session.begin():
        return expire_change_requests(
            SqlAlchemyShiftChangeRequestRepository(session),
            SqlAlchemyShiftChangeTransitionRepository(session),
            SqlAlchemyBookingRepository(session),
            now or utc_now(),
        )


if __name__ == "__main__":
    print(f"Workforce expiry sweep closed {run()} request(s).")

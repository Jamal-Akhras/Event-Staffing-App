from __future__ import annotations

from datetime import datetime

from apps.api.src.datetime_utils import utc_now
from apps.api.src.db.database import SessionLocal
from apps.api.src.repositories.sqlalchemy_worker_certification_repository import (
    SqlAlchemyWorkerCertificationRepository,
)
from apps.api.src.services.certification_expiry import sweep_certification_expiry
from apps.api.src.services.outbox_publisher import SqlAlchemyOutboxPublisher


def run(now: datetime | None = None) -> int:
    with SessionLocal() as session, session.begin():
        return sweep_certification_expiry(
            SqlAlchemyWorkerCertificationRepository(session),
            SqlAlchemyOutboxPublisher(session),
            now or utc_now(),
        )


if __name__ == "__main__":
    print(f"Certification expiry sweep published {run()} notice(s).")

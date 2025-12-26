from __future__ import annotations

import os
from typing import Generator

from apps.api.src.db.database import SessionLocal
from apps.api.src.repositories.booking_repository import BookingRepository
from apps.api.src.repositories.in_memory_booking_repository import InMemoryBookingRepository
from apps.api.src.repositories.in_memory_application_repository import InMemoryApplicationRepository
from apps.api.src.repositories.in_memory_shift_repository import InMemoryShiftRepository
from apps.api.src.repositories.in_memory_worker_profile_repository import InMemoryWorkerProfileRepository
from apps.api.src.repositories.worker_profile_repository import WorkerProfileRepository
from apps.api.src.repositories.shift_repository import ShiftRepository
from apps.api.src.repositories.application_repository import ApplicationRepository
from apps.api.src.repositories.sqlalchemy_booking_repository import (
    SqlAlchemyBookingRepository,
)
from apps.api.src.repositories.sqlalchemy_application_repository import (
    SqlAlchemyApplicationRepository,
)
from apps.api.src.repositories.sqlalchemy_shift_repository import SqlAlchemyShiftRepository
from apps.api.src.repositories.sqlalchemy_worker_profile_repository import (
    SqlAlchemyWorkerProfileRepository,
)

_IN_MEMORY_REPO = InMemoryBookingRepository()
_IN_MEMORY_APPLICATIONS = InMemoryApplicationRepository()
_IN_MEMORY_SHIFTS = InMemoryShiftRepository()
_IN_MEMORY_WORKERS = InMemoryWorkerProfileRepository()


def _use_in_memory() -> bool:
    if os.getenv("USE_IN_MEMORY", "").lower() == "true":
        return True
    return not os.getenv("DATABASE_URL")


def get_booking_repo() -> Generator[BookingRepository, None, None]:
    if _use_in_memory():
        yield _IN_MEMORY_REPO
        return

    session = SessionLocal()
    try:
        yield SqlAlchemyBookingRepository(session)
    finally:
        session.close()


def get_application_repo() -> Generator[ApplicationRepository, None, None]:
    if _use_in_memory():
        yield _IN_MEMORY_APPLICATIONS
        return

    session = SessionLocal()
    try:
        yield SqlAlchemyApplicationRepository(session)
    finally:
        session.close()


def get_shift_repo() -> Generator[ShiftRepository, None, None]:
    if _use_in_memory():
        yield _IN_MEMORY_SHIFTS
        return

    session = SessionLocal()
    try:
        yield SqlAlchemyShiftRepository(session)
    finally:
        session.close()


def get_worker_profile_repo() -> Generator[WorkerProfileRepository, None, None]:
    if _use_in_memory():
        yield _IN_MEMORY_WORKERS
        return

    session = SessionLocal()
    try:
        yield SqlAlchemyWorkerProfileRepository(session)
    finally:
        session.close()


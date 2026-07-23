from __future__ import annotations

import logging
from typing import Generator

from fastapi import Depends

from apps.api.src.config import get_bool_env, get_env
from apps.api.src.db.database import SessionLocal
from apps.api.src.repositories.application_message_history_repository import (
    ApplicationMessageHistoryRepository,
)
from apps.api.src.repositories.booking_repository import BookingRepository
from apps.api.src.repositories.in_memory_application_message_history_repository import (
    InMemoryApplicationMessageHistoryRepository,
)
from apps.api.src.repositories.in_memory_booking_repository import InMemoryBookingRepository
from apps.api.src.repositories.in_memory_application_repository import InMemoryApplicationRepository
from apps.api.src.repositories.in_memory_application_decision_repository import (
    InMemoryApplicationDecisionRepository,
)
from apps.api.src.repositories.in_memory_shift_repository import InMemoryShiftRepository
from apps.api.src.repositories.in_memory_worker_profile_repository import InMemoryWorkerProfileRepository
from apps.api.src.repositories.in_memory_template_repository import InMemoryTemplateRepository
from apps.api.src.repositories.in_memory_message_repository import InMemoryMessageRepository
from apps.api.src.repositories.in_memory_worker_feed_state_repository import (
    InMemoryWorkerFeedStateRepository,
)
from apps.api.src.repositories.worker_profile_repository import WorkerProfileRepository
from apps.api.src.repositories.shift_repository import ShiftRepository
from apps.api.src.repositories.application_repository import ApplicationRepository
from apps.api.src.repositories.application_decision_repository import (
    ApplicationDecisionRepository,
)
from apps.api.src.repositories.sqlalchemy_booking_repository import (
    SqlAlchemyBookingRepository,
)
from apps.api.src.repositories.sqlalchemy_application_repository import (
    SqlAlchemyApplicationRepository,
)
from apps.api.src.repositories.sqlalchemy_application_decision_repository import (
    SqlAlchemyApplicationDecisionRepository,
)
from apps.api.src.repositories.sqlalchemy_application_message_history_repository import (
    SqlAlchemyApplicationMessageHistoryRepository,
)
from apps.api.src.repositories.sqlalchemy_shift_repository import SqlAlchemyShiftRepository
from apps.api.src.repositories.sqlalchemy_worker_profile_repository import (
    SqlAlchemyWorkerProfileRepository,
)
from apps.api.src.repositories.user_repository import UserRepository
from apps.api.src.repositories.in_memory_user_repository import InMemoryUserRepository
from apps.api.src.repositories.sqlalchemy_user_repository import SqlAlchemyUserRepository
from apps.api.src.repositories.account_repository import AccountRepository
from apps.api.src.repositories.in_memory_account_repository import InMemoryAccountRepository
from apps.api.src.repositories.sqlalchemy_account_repository import SqlAlchemyAccountRepository
from apps.api.src.repositories.notification_repository import NotificationRepository
from apps.api.src.repositories.in_memory_notification_repository import InMemoryNotificationRepository
from apps.api.src.repositories.sqlalchemy_notification_repository import SqlAlchemyNotificationRepository
from apps.api.src.repositories.rating_repository import RatingRepository
from apps.api.src.repositories.sqlalchemy_rating_repository import SqlAlchemyRatingRepository
from apps.api.src.repositories.template_repository import TemplateRepository
from apps.api.src.repositories.sqlalchemy_template_repository import SqlAlchemyTemplateRepository
from apps.api.src.repositories.message_repository import MessageRepository
from apps.api.src.repositories.sqlalchemy_message_repository import SqlAlchemyMessageRepository
from apps.api.src.repositories.sqlalchemy_worker_feed_state_repository import (
    SqlAlchemyWorkerFeedStateRepository,
)
from apps.api.src.services.application_service import ApplicationService
from apps.api.src.services.booking_lifecycle_service import BookingLifecycleService
from apps.api.src.services.message_service import MessageService
from apps.api.src.services.shift_service import ShiftService
from apps.api.src.services.template_service import TemplateService
from apps.api.src.services.worker_feed_service import WorkerFeedService

_IN_MEMORY_REPO = InMemoryBookingRepository()
_IN_MEMORY_APPLICATIONS = InMemoryApplicationRepository()
_IN_MEMORY_SHIFTS = InMemoryShiftRepository(_IN_MEMORY_REPO)
_IN_MEMORY_REPO.attach_shift_repo(_IN_MEMORY_SHIFTS)
_IN_MEMORY_APPLICATIONS.attach_shift_repo(_IN_MEMORY_SHIFTS)
_IN_MEMORY_WORKERS = InMemoryWorkerProfileRepository()
_IN_MEMORY_USERS = InMemoryUserRepository()
_IN_MEMORY_TEMPLATES = InMemoryTemplateRepository()
_IN_MEMORY_MESSAGES = InMemoryMessageRepository()
_IN_MEMORY_WORKER_FEED_STATES = InMemoryWorkerFeedStateRepository()
_IN_MEMORY_APPLICATION_MESSAGE_HISTORY = InMemoryApplicationMessageHistoryRepository()
_IN_MEMORY_ACCOUNTS = InMemoryAccountRepository()
_IN_MEMORY_NOTIFICATIONS = InMemoryNotificationRepository()
_IN_MEMORY_APPLICATION_DECISIONS = InMemoryApplicationDecisionRepository(
    _IN_MEMORY_APPLICATIONS,
    _IN_MEMORY_REPO,
    _IN_MEMORY_SHIFTS,
)


def _use_in_memory() -> bool:
    if get_bool_env("USE_IN_MEMORY"):
        return True
    if not get_env("DATABASE_URL"):
        logging.warning(
            "DATABASE_URL is not set — running with in-memory repositories. "
            "All data will be lost on restart. Set DATABASE_URL to persist data."
        )
        return True
    return False


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


def get_application_decision_repo() -> Generator[ApplicationDecisionRepository, None, None]:
    if _use_in_memory():
        yield _IN_MEMORY_APPLICATION_DECISIONS
        return

    session = SessionLocal()
    try:
        yield SqlAlchemyApplicationDecisionRepository(session)
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


def get_user_repo() -> Generator[UserRepository, None, None]:
    if _use_in_memory():
        yield _IN_MEMORY_USERS
        return

    session = SessionLocal()
    try:
        yield SqlAlchemyUserRepository(session)
    finally:
        session.close()


def get_template_repo() -> Generator[TemplateRepository, None, None]:
    if _use_in_memory():
        yield _IN_MEMORY_TEMPLATES
        return

    session = SessionLocal()
    try:
        yield SqlAlchemyTemplateRepository(session)
    finally:
        session.close()


def get_message_repo() -> Generator[MessageRepository, None, None]:
    if _use_in_memory():
        yield _IN_MEMORY_MESSAGES
        return

    session = SessionLocal()
    try:
        yield SqlAlchemyMessageRepository(session)
    finally:
        session.close()


def get_application_message_history_repo() -> Generator[ApplicationMessageHistoryRepository, None, None]:
    if _use_in_memory():
        yield _IN_MEMORY_APPLICATION_MESSAGE_HISTORY
        return

    session = SessionLocal()
    try:
        yield SqlAlchemyApplicationMessageHistoryRepository(session)
    finally:
        session.close()


def get_worker_feed_state_repo():
    if _use_in_memory():
        yield _IN_MEMORY_WORKER_FEED_STATES
        return

    session = SessionLocal()
    try:
        yield SqlAlchemyWorkerFeedStateRepository(session)
    finally:
        session.close()


def _require_database(repo_name: str) -> None:
    if _use_in_memory():
        raise RuntimeError(
            f"{repo_name} has no in-memory implementation; it requires a database. "
            "Unset USE_IN_MEMORY and set DATABASE_URL to use this endpoint."
        )


def get_account_repo() -> Generator[AccountRepository, None, None]:
    if _use_in_memory():
        yield _IN_MEMORY_ACCOUNTS
        return

    session = SessionLocal()
    try:
        yield SqlAlchemyAccountRepository(session)
    finally:
        session.close()


def get_notification_repo() -> Generator[NotificationRepository, None, None]:
    if _use_in_memory():
        yield _IN_MEMORY_NOTIFICATIONS
        return

    session = SessionLocal()
    try:
        yield SqlAlchemyNotificationRepository(session)
    finally:
        session.close()


def get_rating_repo() -> Generator[RatingRepository, None, None]:
    _require_database("RatingRepository")
    session = SessionLocal()
    try:
        yield SqlAlchemyRatingRepository(session)
    finally:
        session.close()


def get_shift_service(
    repo: ShiftRepository = Depends(get_shift_repo),
) -> ShiftService:
    return ShiftService(repo)


def get_application_service(
    application_repo: ApplicationRepository = Depends(get_application_repo),
    shift_repo: ShiftRepository = Depends(get_shift_repo),
    decision_repo: ApplicationDecisionRepository = Depends(get_application_decision_repo),
    history_repo: ApplicationMessageHistoryRepository = Depends(get_application_message_history_repo),
) -> ApplicationService:
    return ApplicationService(
        application_repo,
        shift_repo,
        decision_repo,
        history_repo,
    )


def get_booking_lifecycle_service(
    booking_repo: BookingRepository = Depends(get_booking_repo),
    worker_repo: WorkerProfileRepository = Depends(get_worker_profile_repo),
    shift_repo: ShiftRepository = Depends(get_shift_repo),
) -> BookingLifecycleService:
    return BookingLifecycleService(booking_repo, worker_repo, shift_repo)


def get_template_service(
    template_repo: TemplateRepository = Depends(get_template_repo),
    shift_repo: ShiftRepository = Depends(get_shift_repo),
) -> TemplateService:
    return TemplateService(template_repo, shift_repo)


def get_message_service(
    message_repo: MessageRepository = Depends(get_message_repo),
    shift_repo: ShiftRepository = Depends(get_shift_repo),
    application_repo: ApplicationRepository = Depends(get_application_repo),
    booking_repo: BookingRepository = Depends(get_booking_repo),
) -> MessageService:
    return MessageService(
        message_repo,
        shift_repo,
        application_repo,
        booking_repo,
    )


def get_worker_feed_service(
    repo=Depends(get_worker_feed_state_repo),
    shift_repo: ShiftRepository = Depends(get_shift_repo),
) -> WorkerFeedService:
    return WorkerFeedService(repo, shift_repo)

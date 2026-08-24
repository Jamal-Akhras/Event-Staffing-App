from __future__ import annotations

from fastapi import Depends

from apps.api.src.repositories.application_decision_repository import ApplicationDecisionRepository
from apps.api.src.repositories.application_message_history_repository import ApplicationMessageHistoryRepository
from apps.api.src.repositories.application_repository import ApplicationRepository
from apps.api.src.repositories.booking_repository import BookingRepository
from apps.api.src.repositories.message_repository import MessageRepository
from apps.api.src.repositories.market_repository import MarketRepository
from apps.api.src.repositories.shift_repository import ShiftRepository
from apps.api.src.repositories.template_repository import TemplateRepository
from apps.api.src.repositories.worker_profile_repository import WorkerProfileRepository
from apps.api.src.repositories.worker_feed_query_repository import WorkerFeedQueryRepository
from apps.api.src.repository_dependencies import (
    get_account_repo,
    get_application_decision_repo,
    get_application_message_history_repo,
    get_application_repo,
    get_booking_repo,
    get_message_repo,
    get_market_repo,
    get_notification_repo,
    get_outbox_publisher,
    get_organisation_repo,
    get_rating_repo,
    get_report_repo,
    get_request_session,
    get_request_unit_of_work,
    get_shift_repo,
    get_template_repo,
    get_user_repo,
    get_worker_feed_state_repo,
    get_worker_feed_query_repo,
    get_worker_profile_repo,
)
from apps.api.src.services.application_service import ApplicationService
from apps.api.src.services.booking_lifecycle_service import BookingLifecycleService
from apps.api.src.services.message_service import MessageService
from apps.api.src.services.shift_service import ShiftService
from apps.api.src.services.shift_lifecycle_service import ShiftLifecycleService
from apps.api.src.services.template_service import TemplateService
from apps.api.src.services.worker_feed_service import WorkerFeedService
from apps.api.src.services.worker_shift_feed_service import WorkerShiftFeedService
from apps.api.src.services.outbox_publisher import OutboxPublisher
from apps.api.src.services.idempotency import IdempotencyService

__all__ = [
    "get_account_repo",
    "get_application_decision_repo",
    "get_application_message_history_repo",
    "get_application_repo",
    "get_application_service",
    "get_booking_lifecycle_service",
    "get_booking_repo",
    "get_message_repo",
    "get_message_service",
    "get_idempotency_service",
    "get_market_repo",
    "get_notification_repo",
    "get_outbox_publisher",
    "get_organisation_repo",
    "get_rating_repo",
    "get_report_repo",
    "get_request_session",
    "get_request_unit_of_work",
    "get_shift_repo",
    "get_shift_service",
    "get_shift_lifecycle_service",
    "get_template_repo",
    "get_template_service",
    "get_user_repo",
    "get_worker_feed_service",
    "get_worker_feed_query_repo",
    "get_worker_shift_feed_service",
    "get_worker_feed_state_repo",
    "get_worker_profile_repo",
]


def get_shift_service(repo: ShiftRepository = Depends(get_shift_repo)) -> ShiftService:
    return ShiftService(repo)


def get_idempotency_service(
    session=Depends(get_request_session),
) -> IdempotencyService:
    return IdempotencyService(session)


def get_shift_lifecycle_service(
    shift_repo: ShiftRepository = Depends(get_shift_repo),
    application_repo: ApplicationRepository = Depends(get_application_repo),
    booking_repo: BookingRepository = Depends(get_booking_repo),
    outbox: OutboxPublisher = Depends(get_outbox_publisher),
) -> ShiftLifecycleService:
    return ShiftLifecycleService(shift_repo, application_repo, booking_repo, outbox)


def get_application_service(
    application_repo: ApplicationRepository = Depends(get_application_repo),
    shift_repo: ShiftRepository = Depends(get_shift_repo),
    decision_repo: ApplicationDecisionRepository = Depends(get_application_decision_repo),
    history_repo: ApplicationMessageHistoryRepository = Depends(get_application_message_history_repo),
    outbox: OutboxPublisher = Depends(get_outbox_publisher),
) -> ApplicationService:
    return ApplicationService(application_repo, shift_repo, decision_repo, history_repo, outbox)


def get_booking_lifecycle_service(
    booking_repo: BookingRepository = Depends(get_booking_repo),
    worker_repo: WorkerProfileRepository = Depends(get_worker_profile_repo),
    shift_repo: ShiftRepository = Depends(get_shift_repo),
    outbox: OutboxPublisher = Depends(get_outbox_publisher),
) -> BookingLifecycleService:
    return BookingLifecycleService(booking_repo, worker_repo, shift_repo, outbox)


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
    outbox: OutboxPublisher = Depends(get_outbox_publisher),
) -> MessageService:
    return MessageService(message_repo, shift_repo, application_repo, booking_repo, outbox)


def get_worker_feed_service(
    repo=Depends(get_worker_feed_state_repo),
    shift_repo: ShiftRepository = Depends(get_shift_repo),
) -> WorkerFeedService:
    return WorkerFeedService(repo, shift_repo)


def get_worker_shift_feed_service(
    profile_repo: WorkerProfileRepository = Depends(get_worker_profile_repo),
    market_repo: MarketRepository = Depends(get_market_repo),
    query_repo: WorkerFeedQueryRepository = Depends(get_worker_feed_query_repo),
) -> WorkerShiftFeedService:
    return WorkerShiftFeedService(profile_repo, market_repo, query_repo)

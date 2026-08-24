from __future__ import annotations

from datetime import UTC, datetime, timedelta

from apps.api.src.models.application import Application
from apps.api.src.repositories.in_memory_application_decision_repository import (
    InMemoryApplicationDecisionRepository,
)
from apps.api.src.repositories.in_memory_application_message_history_repository import (
    InMemoryApplicationMessageHistoryRepository,
)
from apps.api.src.repositories.in_memory_application_repository import InMemoryApplicationRepository
from apps.api.src.repositories.in_memory_booking_repository import InMemoryBookingRepository
from apps.api.src.repositories.in_memory_notification_repository import InMemoryNotificationRepository
from apps.api.src.repositories.in_memory_shift_repository import InMemoryShiftRepository
from apps.api.src.services.application_service import ApplicationService
from apps.api.src.services.email import LoggingEmailTransport
from apps.api.src.services.outbox_publisher import InMemoryOutboxPublisher


def test_list_applications_by_worker_filters_before_limit():
    application_repo = InMemoryApplicationRepository()
    booking_repo = InMemoryBookingRepository()
    shift_repo = InMemoryShiftRepository(booking_repo)
    service = ApplicationService(
        application_repo,
        shift_repo,
        InMemoryApplicationDecisionRepository(application_repo, booking_repo, shift_repo),
        InMemoryApplicationMessageHistoryRepository(),
        InMemoryOutboxPublisher(InMemoryNotificationRepository(), LoggingEmailTransport()),
    )
    now = datetime(2030, 1, 1, 12, 0, 0, tzinfo=UTC)
    application_repo.save(_application("target-app", "target-worker", "target-shift", now))
    for index in range(60):
        application_repo.save(
            _application(
                f"other-app-{index}",
                "other-worker",
                f"other-shift-{index}",
                now + timedelta(minutes=index + 1),
            )
        )

    results = service.list_applications(worker_id="target-worker", limit=50)

    assert [application.application_id for application in results] == ["target-app"]


def _application(application_id: str, worker_id: str, shift_id: str, created_at: datetime) -> Application:
    return Application(
        application_id=application_id,
        shift_id=shift_id,
        worker_id=worker_id,
        operator_id="operator-1",
        start_time=created_at,
        end_time=created_at + timedelta(hours=4),
        message=None,
        booking_id=None,
        status="applied",
        created_at=created_at,
    )

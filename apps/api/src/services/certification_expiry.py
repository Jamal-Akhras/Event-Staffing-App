from __future__ import annotations

from datetime import datetime, timedelta

from apps.api.src.models.worker_certification import WorkerCertification
from apps.api.src.repositories.worker_certification_repository import (
    WorkerCertificationRepository,
)
from apps.api.src.services.outbox_publisher import OutboxPublisher

STAGES = (
    ("certification.expired", timedelta(days=-3650), timedelta(0), "has expired"),
    ("certification.expiring_7d", timedelta(0), timedelta(days=7), "expires within a week"),
    ("certification.expiring_30d", timedelta(days=7), timedelta(days=30), "expires within a month"),
)


def sweep_certification_expiry(
    certifications: WorkerCertificationRepository,
    outbox: OutboxPublisher,
    now: datetime,
) -> int:
    published = 0
    for event_type, from_offset, to_offset, phrase in STAGES:
        for certification in certifications.list_expiring_between(
            now + from_offset, now + to_offset
        ):
            _publish(outbox, event_type, certification, phrase)
            published += 1
    return published


def _publish(
    outbox: OutboxPublisher, event_type: str, certification: WorkerCertification, phrase: str
) -> None:
    outbox.publish_notification(
        event_type=event_type,
        aggregate_type="worker_certification",
        aggregate_id=certification.certification_id,
        recipient_kind="worker",
        recipient_id=certification.worker_id,
        category="certifications",
        title=f"Your {certification.display_name} {phrase}",
        body="Renew it to keep taking shifts that require it.",
        action_kind=None,
        action_entity_id=None,
    )

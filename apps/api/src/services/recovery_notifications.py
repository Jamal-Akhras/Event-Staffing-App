from __future__ import annotations

from apps.api.src.services.outbox_publisher import OutboxPublisher


def notify_worker(
    publisher: OutboxPublisher,
    worker_id: str,
    shift_id: str,
    notification_type: str,
    title: str,
    body: str,
) -> None:
    publisher.publish_notification(
        event_type=notification_type,
        aggregate_type="shift",
        aggregate_id=f"{shift_id}:{worker_id}",
        recipient_kind="worker",
        recipient_id=worker_id,
        category="shift_changes",
        title=title,
        body=body,
        action_kind="shift",
        action_entity_id=shift_id,
    )

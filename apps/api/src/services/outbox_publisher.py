from __future__ import annotations

from hashlib import sha256
from typing import Protocol
from uuid import uuid4

from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import insert as postgresql_insert

from apps.api.src.datetime_utils import utc_now
from apps.api.src.db.notification_models import OutboxEventModel
from apps.api.src.models.notification import Notification
from apps.api.src.repositories.notification_repository import NotificationRepository
from apps.api.src.services.email import Email, EmailTransport


class OutboxPublisher(Protocol):
    def publish_notification(
        self,
        *,
        event_type: str,
        aggregate_type: str,
        aggregate_id: str,
        recipient_kind: str,
        recipient_id: str,
        category: str,
        title: str,
        body: str,
        action_kind: str | None = None,
        action_entity_id: str | None = None,
    ) -> None: ...

    def publish_email(
        self,
        *,
        event_type: str,
        aggregate_type: str,
        aggregate_id: str,
        email: Email,
        idempotency_suffix: str,
    ) -> None: ...


class SqlAlchemyOutboxPublisher:
    def __init__(self, session: Session) -> None:
        self._session = session

    def publish_notification(
        self,
        *,
        event_type: str,
        aggregate_type: str,
        aggregate_id: str,
        recipient_kind: str,
        recipient_id: str,
        category: str,
        title: str,
        body: str,
        action_kind: str | None = None,
        action_entity_id: str | None = None,
    ) -> None:
        payload = {
            "category": category,
            "recipients": [{"kind": recipient_kind, "id": recipient_id}],
            "channels": ["in_app", "push"],
            "notification": {
                "type": event_type,
                "title": title,
                "body": body,
                "action": (
                    {"kind": action_kind, "entity_id": action_entity_id}
                    if action_kind and action_entity_id
                    else None
                ),
            },
        }
        key = _idempotency_key(
            event_type,
            aggregate_type,
            aggregate_id,
            recipient_kind,
            recipient_id,
        )
        self._save(event_type, aggregate_type, aggregate_id, payload, key)

    def publish_email(
        self,
        *,
        event_type: str,
        aggregate_type: str,
        aggregate_id: str,
        email: Email,
        idempotency_suffix: str,
    ) -> None:
        payload = {
            "category": "account",
            "recipients": [{"kind": "email", "id": email.to_address}],
            "channels": ["email"],
            "email": {"subject": email.subject, "body": email.body},
            "transactional": True,
        }
        key = _idempotency_key(event_type, aggregate_type, aggregate_id, idempotency_suffix)
        self._save(event_type, aggregate_type, aggregate_id, payload, key)

    def _save(
        self,
        event_type: str,
        aggregate_type: str,
        aggregate_id: str,
        payload: dict[str, object],
        idempotency_key: str,
    ) -> None:
        now = utc_now()
        values = {
            "event_id": str(uuid4()),
            "event_type": event_type,
            "aggregate_type": aggregate_type,
            "aggregate_id": aggregate_id,
            "payload": payload,
            "idempotency_key": idempotency_key,
            "occurred_at": now,
            "available_at": now,
            "attempt_count": 0,
        }
        if self._session.get_bind().dialect.name == "postgresql":
            statement = (
                postgresql_insert(OutboxEventModel)
                .values(**values)
                .on_conflict_do_nothing(index_elements=["idempotency_key"])
            )
            self._session.execute(statement)
            self._session.flush()
            return
        existing = (
            self._session.query(OutboxEventModel.event_id)
            .filter(OutboxEventModel.idempotency_key == idempotency_key)
            .scalar()
        )
        if existing:
            return
        self._session.add(OutboxEventModel(**values))
        self._session.flush()


class InMemoryOutboxPublisher:
    def __init__(
        self,
        notifications: NotificationRepository,
        email_transport: EmailTransport,
    ) -> None:
        self._notifications = notifications
        self._email_transport = email_transport
        self._keys: set[str] = set()

    def publish_notification(
        self,
        *,
        event_type: str,
        aggregate_type: str,
        aggregate_id: str,
        recipient_kind: str,
        recipient_id: str,
        category: str,
        title: str,
        body: str,
        action_kind: str | None = None,
        action_entity_id: str | None = None,
    ) -> None:
        key = _idempotency_key(
            event_type,
            aggregate_type,
            aggregate_id,
            recipient_kind,
            recipient_id,
        )
        if key in self._keys:
            return
        self._keys.add(key)
        self._notifications.save(
            Notification(
                notification_id=str(uuid4()),
                worker_id=recipient_id if recipient_kind == "worker" else None,
                venue_id=recipient_id if recipient_kind == "venue" else None,
                type=event_type,
                title=title,
                body=body,
                action_kind=action_kind,
                action_entity_id=action_entity_id,
                shift_id=action_entity_id if action_kind == "shift" else None,
                created_at=utc_now(),
            )
        )

    def publish_email(
        self,
        *,
        event_type: str,
        aggregate_type: str,
        aggregate_id: str,
        email: Email,
        idempotency_suffix: str,
    ) -> None:
        key = _idempotency_key(event_type, aggregate_type, aggregate_id, idempotency_suffix)
        if key in self._keys:
            return
        self._keys.add(key)
        self._email_transport.send(email)


def _idempotency_key(event_type: str, *parts: str) -> str:
    digest = sha256(":".join(parts).encode("utf-8")).hexdigest()
    return f"{event_type}:{digest}"

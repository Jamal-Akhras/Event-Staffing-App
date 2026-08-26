from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import timedelta
from uuid import uuid4

from sqlalchemy import or_
from sqlalchemy.orm import sessionmaker

from apps.api.src.datetime_utils import utc_now
from apps.api.src.db.notification_models import (
    NotificationDeliveryModel,
    NotificationModel,
    OutboxEventModel,
    PushTokenModel,
)
from apps.api.src.services.email import Email, EmailTransport, get_email_transport
from apps.api.src.services.expo_push import send_expo_push
from apps.api.src.services.outbox_recipients import channel_enabled, push_tokens

log = logging.getLogger(__name__)
LEASE_DURATION = timedelta(minutes=5)
MAX_ATTEMPTS = 8


@dataclass(frozen=True)
class DispatchStats:
    events_fanned_out: int = 0
    deliveries_sent: int = 0
    deliveries_failed: int = 0


def dispatch_outbox_once(
    session_factory: sessionmaker,
    worker_id: str,
    batch_size: int = 50,
    email_transport: EmailTransport | None = None,
) -> DispatchStats:
    transport = email_transport or get_email_transport()
    event_ids = _claim_events(session_factory, worker_id, batch_size)
    fanned_out = sum(_fan_out_event(session_factory, event_id, worker_id) for event_id in event_ids)
    delivery_ids = _claim_deliveries(session_factory, worker_id, batch_size)
    sent = 0
    failed = 0
    for delivery_id in delivery_ids:
        try:
            _deliver(session_factory, delivery_id, worker_id, transport)
            sent += 1
        except Exception as exc:
            failed += 1
            _record_delivery_failure(session_factory, delivery_id, worker_id, exc)
            log.exception("outbox delivery failed: delivery_id=%s", delivery_id)
    return DispatchStats(fanned_out, sent, failed)


def _claim_events(session_factory: sessionmaker, worker_id: str, limit: int) -> list[str]:
    now = utc_now()
    stale = now - LEASE_DURATION
    with session_factory() as session, session.begin():
        rows = (
            session.query(OutboxEventModel)
            .filter(
                OutboxEventModel.processed_at.is_(None),
                OutboxEventModel.dead_lettered_at.is_(None),
                OutboxEventModel.available_at <= now,
                or_(OutboxEventModel.locked_at.is_(None), OutboxEventModel.locked_at < stale),
            )
            .order_by(OutboxEventModel.occurred_at, OutboxEventModel.event_id)
            .with_for_update(skip_locked=True)
            .limit(limit)
            .all()
        )
        for row in rows:
            row.locked_at = now
            row.locked_by = worker_id
        return [row.event_id for row in rows]


def _fan_out_event(session_factory: sessionmaker, event_id: str, worker_id: str) -> int:
    try:
        with session_factory() as session, session.begin():
            event = session.get(OutboxEventModel, event_id)
            if event is None or event.processed_at is not None or event.locked_by != worker_id:
                return 0
            payload = event.payload
            for recipient in payload["recipients"]:
                for channel in payload["channels"]:
                    if not channel_enabled(session, recipient, channel, payload):
                        continue
                    key = f"{event.event_id}:{recipient['kind']}:{recipient['id']}:{channel}"
                    exists = (
                        session.query(NotificationDeliveryModel.delivery_id)
                        .filter(NotificationDeliveryModel.idempotency_key == key)
                        .scalar()
                    )
                    if exists:
                        continue
                    session.add(
                        NotificationDeliveryModel(
                            delivery_id=str(uuid4()),
                            event_id=event.event_id,
                            recipient_kind=recipient["kind"],
                            recipient_id=recipient["id"],
                            channel=channel,
                            status="pending",
                            attempt_count=0,
                            next_attempt_at=utc_now(),
                            idempotency_key=key,
                        )
                    )
            event.processed_at = utc_now()
            event.locked_at = None
            event.locked_by = None
            event.last_error = None
        return 1
    except Exception as exc:
        _record_event_failure(session_factory, event_id, worker_id, exc)
        log.exception("outbox fan-out failed: event_id=%s", event_id)
        return 0


def _claim_deliveries(session_factory: sessionmaker, worker_id: str, limit: int) -> list[str]:
    now = utc_now()
    stale = now - LEASE_DURATION
    with session_factory() as session, session.begin():
        rows = (
            session.query(NotificationDeliveryModel)
            .filter(
                NotificationDeliveryModel.status == "pending",
                NotificationDeliveryModel.next_attempt_at <= now,
                or_(
                    NotificationDeliveryModel.locked_at.is_(None),
                    NotificationDeliveryModel.locked_at < stale,
                ),
            )
            .order_by(NotificationDeliveryModel.next_attempt_at, NotificationDeliveryModel.delivery_id)
            .with_for_update(skip_locked=True)
            .limit(limit)
            .all()
        )
        for row in rows:
            row.locked_at = now
            row.locked_by = worker_id
        return [row.delivery_id for row in rows]


def _deliver(
    session_factory: sessionmaker,
    delivery_id: str,
    worker_id: str,
    email_transport: EmailTransport,
) -> None:
    with session_factory() as session:
        delivery = _claimed_delivery(session, delivery_id, worker_id)
        if delivery is None:
            return
        event = session.get(OutboxEventModel, delivery.event_id)
        if event is None:
            raise RuntimeError("Outbox event no longer exists.")
        channel = delivery.channel
        recipient_kind = delivery.recipient_kind
        recipient_id = delivery.recipient_id
        payload = dict(event.payload)
        if channel == "push":
            tokens = push_tokens(session, recipient_kind, recipient_id, payload)
        else:
            tokens = []
    if channel == "in_app":
        _deliver_in_app(session_factory, delivery_id, worker_id, recipient_kind, recipient_id, payload)
        return
    if channel == "email":
        content = payload["email"]
        email_transport.send(Email(recipient_id, content["subject"], content["body"]))
    elif channel == "push":
        content = payload["notification"]
        dead_tokens = send_expo_push(tokens, content["title"], content["body"], content.get("action") or {})
        if dead_tokens:
            _revoke_push_tokens(session_factory, dead_tokens)
    _mark_delivery_success(session_factory, delivery_id, worker_id)


def _revoke_push_tokens(session_factory: sessionmaker, tokens: list[str]) -> None:
    with session_factory() as session, session.begin():
        session.query(PushTokenModel).filter(
            PushTokenModel.token.in_(tokens),
            PushTokenModel.revoked_at.is_(None),
        ).update({"revoked_at": utc_now()}, synchronize_session=False)


def _deliver_in_app(
    session_factory: sessionmaker,
    delivery_id: str,
    worker_id: str,
    recipient_kind: str,
    recipient_id: str,
    payload: dict,
) -> None:
    with session_factory() as session, session.begin():
        delivery = _claimed_delivery(session, delivery_id, worker_id)
        if delivery is None:
            return
        existing = (
            session.query(NotificationModel.notification_id)
            .filter(NotificationModel.delivery_id == delivery_id)
            .scalar()
        )
        if not existing:
            content = payload["notification"]
            action = content.get("action") or {}
            session.add(
                NotificationModel(
                    notification_id=str(uuid4()),
                    worker_id=recipient_id if recipient_kind == "worker" else None,
                    venue_id=recipient_id if recipient_kind == "venue" else None,
                    type=content["type"],
                    title=content["title"],
                    body=content["body"],
                    shift_id=action.get("entity_id") if action.get("kind") == "shift" else None,
                    action_kind=action.get("kind"),
                    action_entity_id=action.get("entity_id"),
                    delivery_id=delivery_id,
                    read=False,
                    created_at=utc_now(),
                )
            )
        _mark_delivered(delivery)


def _mark_delivery_success(session_factory: sessionmaker, delivery_id: str, worker_id: str) -> None:
    with session_factory() as session, session.begin():
        delivery = _claimed_delivery(session, delivery_id, worker_id)
        if delivery is not None:
            _mark_delivered(delivery)


def _claimed_delivery(session, delivery_id: str, worker_id: str) -> NotificationDeliveryModel | None:
    delivery = session.get(NotificationDeliveryModel, delivery_id)
    if delivery is None or delivery.status != "pending" or delivery.locked_by != worker_id:
        return None
    return delivery


def _mark_delivered(delivery: NotificationDeliveryModel) -> None:
    delivery.status = "delivered"
    delivery.delivered_at = utc_now()
    delivery.locked_at = None
    delivery.locked_by = None
    delivery.last_error = None


def _record_event_failure(session_factory: sessionmaker, event_id: str, worker_id: str, exc: Exception) -> None:
    with session_factory() as session, session.begin():
        event = session.get(OutboxEventModel, event_id)
        if event is None or event.locked_by != worker_id:
            return
        if _release_with_failure(event, exc):
            event.dead_lettered_at = utc_now()
        else:
            event.available_at = utc_now() + _retry_delay(event.attempt_count)


def _record_delivery_failure(
    session_factory: sessionmaker,
    delivery_id: str,
    worker_id: str,
    exc: Exception,
) -> None:
    with session_factory() as session, session.begin():
        delivery = session.get(NotificationDeliveryModel, delivery_id)
        if delivery is None or delivery.locked_by != worker_id:
            return
        if _release_with_failure(delivery, exc):
            delivery.status = "dead_letter"
        else:
            delivery.next_attempt_at = utc_now() + _retry_delay(delivery.attempt_count)


def _release_with_failure(row, exc: Exception) -> bool:
    row.attempt_count += 1
    row.last_error = str(exc)[:1000]
    row.locked_at = None
    row.locked_by = None
    return row.attempt_count >= MAX_ATTEMPTS


def _retry_delay(attempt_count: int) -> timedelta:
    return timedelta(seconds=min(3600, 30 * (2 ** max(0, attempt_count - 1))))

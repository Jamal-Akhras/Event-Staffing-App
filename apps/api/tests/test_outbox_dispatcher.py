from __future__ import annotations

from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from apps.api.src.db import models  # noqa: F401
from apps.api.src.db.database import Base
from apps.api.src.db.notification_models import (
    NotificationDeliveryModel,
    NotificationModel,
    OutboxEventModel,
)
from apps.api.src.datetime_utils import utc_now
from apps.api.src.services.email import Email
from apps.api.src.services.outbox_dispatcher import dispatch_outbox_once
from apps.api.src.services.outbox_publisher import SqlAlchemyOutboxPublisher


class RecordingTransport:
    def __init__(self) -> None:
        self.sent: list[Email] = []

    def send(self, email: Email) -> None:
        self.sent.append(email)


class FailingTransport:
    def send(self, _email: Email) -> None:
        raise RuntimeError("smtp unavailable")


def _session_factory():
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        future=True,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


def test_domain_rollback_removes_outbox_event():
    factory = _session_factory()
    try:
        with factory() as session:
            try:
                with session.begin():
                    _publish_worker_notification(session)
                    raise RuntimeError("domain write failed")
            except RuntimeError:
                pass
        with factory() as session:
            assert session.scalar(select(func.count()).select_from(OutboxEventModel)) == 0
    finally:
        factory.kw["bind"].dispose()


def test_replay_is_idempotent_and_materializes_one_notification():
    factory = _session_factory()
    try:
        with factory() as session, session.begin():
            _publish_worker_notification(session)
            _publish_worker_notification(session)
        stats = dispatch_outbox_once(factory, "worker-a", email_transport=RecordingTransport())
        assert stats.events_fanned_out == 1
        assert stats.deliveries_sent == 1
        dispatch_outbox_once(factory, "worker-b", email_transport=RecordingTransport())
        with factory() as session:
            assert session.scalar(select(func.count()).select_from(OutboxEventModel)) == 1
            assert session.scalar(select(func.count()).select_from(NotificationDeliveryModel)) == 1
            assert session.scalar(select(func.count()).select_from(NotificationModel)) == 1
    finally:
        factory.kw["bind"].dispose()


def test_failed_email_is_released_for_retry():
    factory = _session_factory()
    try:
        with factory() as session, session.begin():
            SqlAlchemyOutboxPublisher(session).publish_email(
                event_type="auth.reset_password",
                aggregate_type="user",
                aggregate_id="user-1",
                email=Email("worker@example.com", "Reset", "Open the link"),
                idempotency_suffix="token-1",
            )
        stats = dispatch_outbox_once(factory, "worker-a", email_transport=FailingTransport())
        assert stats.deliveries_failed == 1
        with factory() as session:
            delivery = session.scalar(select(NotificationDeliveryModel))
            assert delivery.status == "pending"
            assert delivery.attempt_count == 1
            assert delivery.locked_at is None
            assert delivery.next_attempt_at > utc_now()
    finally:
        factory.kw["bind"].dispose()


def _publish_worker_notification(session) -> None:
    SqlAlchemyOutboxPublisher(session).publish_notification(
        event_type="application.approved",
        aggregate_type="application",
        aggregate_id="application-1",
        recipient_kind="worker",
        recipient_id="worker-1",
        category="applications",
        title="Application approved",
        body="You are booked.",
        action_kind="application",
        action_entity_id="application-1",
    )

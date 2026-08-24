from __future__ import annotations

from datetime import timedelta
from threading import Barrier, Thread

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select

from apps.api.src.datetime_utils import utc_now
from apps.api.src.db.notification_models import (
    NotificationDeliveryModel,
    NotificationModel,
    OutboxEventModel,
)
from apps.api.src.services.email import Email
from apps.api.src.services.outbox_dispatcher import MAX_ATTEMPTS, dispatch_outbox_once
from apps.api.src.services.outbox_publisher import SqlAlchemyOutboxPublisher
from apps.api.src.main import app
from apps.api.tests.test_postgres_flows import _auth, _register_worker

pytestmark = pytest.mark.postgres


class FailingTransport:
    def send(self, _email: Email) -> None:
        raise RuntimeError("smtp unavailable")


def test_two_dispatchers_materialize_one_in_app_notification():
    from apps.api.src.db.database import SessionLocal

    with SessionLocal() as session, session.begin():
        _publish_notification(session)

    barrier = Barrier(2)
    errors: list[Exception] = []

    def dispatch(worker_id: str) -> None:
        try:
            barrier.wait()
            dispatch_outbox_once(SessionLocal, worker_id)
        except Exception as exc:
            errors.append(exc)

    threads = [Thread(target=dispatch, args=(f"dispatcher-{index}",)) for index in range(2)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert errors == []
    with SessionLocal() as session:
        assert session.scalar(select(func.count()).select_from(OutboxEventModel)) == 1
        assert session.scalar(select(func.count()).select_from(NotificationDeliveryModel)) == 1
        assert session.scalar(select(func.count()).select_from(NotificationModel)) == 1


def test_concurrent_producers_share_one_idempotent_event():
    from apps.api.src.db.database import SessionLocal

    barrier = Barrier(2)
    errors: list[Exception] = []

    def publish() -> None:
        try:
            barrier.wait()
            with SessionLocal() as session, session.begin():
                _publish_notification(session)
        except Exception as exc:
            errors.append(exc)

    threads = [Thread(target=publish) for _ in range(2)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert errors == []
    with SessionLocal() as session:
        assert session.scalar(select(func.count()).select_from(OutboxEventModel)) == 1


def test_stale_event_lease_is_reclaimed():
    from apps.api.src.db.database import SessionLocal

    with SessionLocal() as session, session.begin():
        _publish_notification(session)
        event = session.scalar(select(OutboxEventModel))
        event.locked_by = "dead-worker"
        event.locked_at = utc_now() - timedelta(minutes=10)

    stats = dispatch_outbox_once(SessionLocal, "replacement-worker")
    assert stats.events_fanned_out == 1
    with SessionLocal() as session:
        event = session.scalar(select(OutboxEventModel))
        assert event.processed_at is not None
        assert event.locked_by is None


def test_actor_notification_preferences_and_devices_are_tenant_scoped():
    from apps.api.src.db.database import SessionLocal

    client = TestClient(app)
    worker = _register_worker(client, "outbox-worker@example.com")
    other_worker = _register_worker(client, "other-outbox-worker@example.com")
    with SessionLocal() as session, session.begin():
        SqlAlchemyOutboxPublisher(session).publish_notification(
            event_type="application.approved",
            aggregate_type="application",
            aggregate_id="scoped-application",
            recipient_kind="worker",
            recipient_id=worker["worker_profile_id"],
            category="applications",
            title="Application approved",
            body="You are booked.",
            action_kind="application",
            action_entity_id="scoped-application",
        )
    dispatch_outbox_once(SessionLocal, "scope-worker")

    inbox = client.get("/notifications", headers=_auth(worker))
    assert inbox.status_code == 200
    notification_id = inbox.json()["items"][0]["notification_id"]
    assert inbox.json()["unread_count"] == 1
    assert client.post(
        f"/notifications/{notification_id}/read",
        headers=_auth(other_worker),
    ).status_code == 404

    preferences = client.get("/notification-preferences", headers=_auth(worker)).json()
    preferences["channels"]["push"] = False
    saved = client.put(
        "/notification-preferences",
        headers=_auth(worker),
        json=preferences,
    )
    assert saved.status_code == 200
    assert saved.json()["channels"]["push"] is False

    token = client.post(
        "/devices/push-tokens",
        headers=_auth(worker),
        json={"token": "ExponentPushToken[scope]", "platform": "android", "device_id": "phone-1"},
    )
    assert token.status_code == 200
    token_id = token.json()["push_token_id"]
    assert client.delete(
        f"/devices/push-tokens/{token_id}",
        headers=_auth(other_worker),
    ).status_code == 404
    assert client.delete(
        f"/devices/push-tokens/{token_id}",
        headers=_auth(worker),
    ).status_code == 200


def test_email_delivery_reaches_dead_letter_after_max_attempts():
    from apps.api.src.db.database import SessionLocal

    with SessionLocal() as session, session.begin():
        SqlAlchemyOutboxPublisher(session).publish_email(
            event_type="auth.reset_password",
            aggregate_type="user",
            aggregate_id="user-1",
            email=Email("worker@example.com", "Reset", "Open the link"),
            idempotency_suffix="token-1",
        )

    for index in range(MAX_ATTEMPTS):
        dispatch_outbox_once(SessionLocal, f"worker-{index}", email_transport=FailingTransport())
        with SessionLocal() as session, session.begin():
            delivery = session.scalar(select(NotificationDeliveryModel))
            if delivery.status == "pending":
                delivery.next_attempt_at = utc_now() - timedelta(seconds=1)

    with SessionLocal() as session:
        delivery = session.scalar(select(NotificationDeliveryModel))
        assert delivery.status == "dead_letter"
        assert delivery.attempt_count == MAX_ATTEMPTS
        assert delivery.locked_by is None


def _publish_notification(session) -> None:
    publisher = SqlAlchemyOutboxPublisher(session)
    publisher.publish_notification(
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
    publisher.publish_notification(
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

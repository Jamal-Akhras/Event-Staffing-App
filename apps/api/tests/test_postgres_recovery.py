from __future__ import annotations

from datetime import timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from apps.api.src import main
from apps.api.src.db.models import ApplicationModel, BookingModel, NotificationModel, ShiftModel
from apps.api.src.deps import get_outbox_publisher
from apps.api.src.services.outbox_dispatcher import dispatch_outbox_once
from apps.api.tests.test_postgres_flows import (
    BASE_NOW,
    _apply,
    _approve,
    _auth,
    _create_shift,
    _register_verified_operator,
    _register_worker,
)
from packages.domain.src.booking_state import BookingState

pytestmark = pytest.mark.postgres


@pytest.fixture()
def client(monkeypatch):
    monkeypatch.setenv("OPERATOR_INVITE_CODES", "pg-test-invite")
    monkeypatch.setattr("apps.api.src.routes.shifts.geocode", lambda location: (None, None))
    return TestClient(main.app)


def _db_session():
    from apps.api.src.db.database import SessionLocal

    return SessionLocal()


def _staffed_shift(client: TestClient):
    operator = _register_verified_operator(client, "recovery-operator@pg-test.example")
    booked_worker = _register_worker(client, "recovery-booked@pg-test.example")
    pending_worker = _register_worker(client, "recovery-pending@pg-test.example")
    shift = _create_shift(client, operator, workers_needed=2)
    approved = _approve(client, operator, _apply(client, booked_worker, shift["shift_id"])["application_id"])
    assert approved.status_code == 200, approved.text
    pending = _apply(client, pending_worker, shift["shift_id"])
    return operator, booked_worker, pending_worker, shift, approved.json(), pending


def test_shift_cancellation_persists_audit_and_related_updates(client: TestClient):
    operator, booked_worker, pending_worker, shift, approved, pending = _staffed_shift(client)
    cancelled_at = BASE_NOW + timedelta(hours=1, minutes=30)

    response = client.post(
        f"/shifts/{shift['shift_id']}/cancel",
        json={"reason": "Emergency venue closure", "now": cancelled_at.isoformat()},
        headers=_auth(operator),
    )
    assert response.status_code == 200, response.text

    from apps.api.src.db.database import SessionLocal

    dispatch_outbox_once(SessionLocal, "recovery-test")

    with _db_session() as session:
        stored_shift = session.get(ShiftModel, shift["shift_id"])
        assert stored_shift.status == "cancelled"
        assert stored_shift.workers_filled == 0
        assert stored_shift.cancelled_at == cancelled_at
        assert stored_shift.cancellation_reason == "Emergency venue closure"
        assert stored_shift.cancelled_by_user_id == operator["user_id"]

        booking = session.get(BookingModel, approved["booking_id"])
        assert booking.state == BookingState.CANCELLED_BY_OPERATOR
        assert booking.cancellation_reason == "Emergency venue closure"
        assert booking.cancelled_by_user_id == operator["user_id"]
        assert session.get(ApplicationModel, pending["application_id"]).status == "rejected"

        recipients = set(
            session.execute(
                select(NotificationModel.worker_id).where(NotificationModel.shift_id == shift["shift_id"])
            ).scalars()
        )
        assert booked_worker["worker_profile_id"] in recipients
        assert pending_worker["worker_profile_id"] in recipients


def test_notification_failure_rolls_back_whole_shift_cancellation(client: TestClient):
    operator, _, _, shift, approved, pending = _staffed_shift(client)

    class FailingOutboxPublisher:
        def publish_notification(self, **_kwargs):
            raise RuntimeError("outbox persistence failed")

        def publish_email(self, **_kwargs):
            raise RuntimeError("outbox persistence failed")

    main.app.dependency_overrides[get_outbox_publisher] = FailingOutboxPublisher
    rollback_client = TestClient(main.app, raise_server_exceptions=False)
    response = rollback_client.post(
        f"/shifts/{shift['shift_id']}/cancel",
        json={
            "reason": "Emergency venue closure",
            "now": (BASE_NOW + timedelta(hours=1, minutes=30)).isoformat(),
        },
        headers=_auth(operator),
    )
    assert response.status_code == 500

    with _db_session() as session:
        stored_shift = session.get(ShiftModel, shift["shift_id"])
        assert stored_shift.status == "open"
        assert stored_shift.workers_filled == 1
        assert session.get(BookingModel, approved["booking_id"]).state == BookingState.CONFIRMED
        assert session.get(ApplicationModel, pending["application_id"]).status == "applied"


def test_worker_withdrawal_is_persisted_with_reason(client: TestClient):
    operator = _register_verified_operator(client, "withdraw-operator@pg-test.example")
    worker = _register_worker(client, "withdraw-worker@pg-test.example")
    shift = _create_shift(client, operator)
    application = _apply(client, worker, shift["shift_id"])
    withdrawn_at = BASE_NOW + timedelta(hours=1)

    response = client.post(
        f"/applications/{application['application_id']}/withdraw",
        json={"reason": "Schedule changed", "now": withdrawn_at.isoformat()},
        headers=_auth(worker),
    )
    assert response.status_code == 200, response.text

    with _db_session() as session:
        stored = session.get(ApplicationModel, application["application_id"])
        assert stored.status == "withdrawn"
        assert stored.withdrawn_at == withdrawn_at
        assert stored.withdrawal_reason == "Schedule changed"

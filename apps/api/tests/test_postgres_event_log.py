from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from apps.api.src import main
from apps.api.src.db.event_models import EventModel

pytestmark = pytest.mark.postgres

WORKER = {"X-Actor-Role": "worker", "X-Actor-Id": "worker-1", "X-Client": "mobile", "X-Session-Id": "pg-session"}


def _stored(name: str) -> list[EventModel]:
    from apps.api.src.db.database import SessionLocal

    with SessionLocal() as session:
        return list(session.execute(select(EventModel).where(EventModel.name == name)).scalars().all())


def test_events_persist_to_postgres_with_client_context():
    client = TestClient(main.app)
    response = client.post(
        "/events",
        json={"events": [{"name": "shift.viewed", "subject_type": "shift", "subject_id": "shift-9"}]},
        headers=WORKER,
    )
    assert response.status_code == 202

    rows = _stored("shift.viewed")
    assert len(rows) == 1
    assert rows[0].source == "mobile"
    assert rows[0].session_id == "pg-session"
    assert rows[0].worker_id == "worker-1"


def test_failed_requests_still_leave_an_audit_trail():
    client = TestClient(main.app)
    client.post("/auth/login", json={"email": "nobody@example.com", "password": "wrong-password"})

    failures = _stored("auth.login_failed")
    assert len(failures) == 1
    assert failures[0].context["reason"] == "invalid_credentials"

    audit = [row for row in _stored("http.request") if row.subject_id == "/auth/login"]
    assert audit and audit[0].status_code == 401


def test_pagination_walks_backwards_without_repeating():
    client = TestClient(main.app)
    client.post(
        "/events",
        json={"events": [{"name": "feed.scrolled", "context": {"page": page}} for page in range(5)]},
        headers=WORKER,
    )
    system = {"X-Actor-Role": "system", "X-Actor-Id": "system"}

    first = client.get("/system/events?name=feed.scrolled&limit=2", headers=system).json()
    assert len(first["events"]) == 2
    assert first["next_before_id"]

    second = client.get(
        f"/system/events?name=feed.scrolled&limit=2&before_id={first['next_before_id']}", headers=system
    ).json()
    assert len(second["events"]) == 2
    seen = {event["event_id"] for event in first["events"]} & {event["event_id"] for event in second["events"]}
    assert seen == set()

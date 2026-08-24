from __future__ import annotations

from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient

from apps.api.src.config import use_in_memory_repositories
from apps.api.src.main import app
from apps.api.src.services.idempotency import IdempotencyConflict, IdempotencyService
from apps.api.tests.test_postgres_flows import (
    INVITE_CODE,
    _auth,
    _register_verified_operator,
)


def test_in_memory_idempotency_replays_and_rejects_payload_changes() -> None:
    service = IdempotencyService(None)
    first = service.start("user-1", "message.create", "retry-1", {"content": "hello"})
    service.finish(first.record_id, {"message_id": "message-1"})

    replay = service.start("user-1", "message.create", "retry-1", {"content": "hello"})

    assert replay.cached_response == {"message_id": "message-1"}
    try:
        service.start("user-1", "message.create", "retry-1", {"content": "changed"})
    except IdempotencyConflict:
        pass
    else:
        raise AssertionError("Reusing an idempotency key with different input must fail.")


def test_shift_creation_replays_same_response(monkeypatch) -> None:
    monkeypatch.setattr("apps.api.src.routes.shifts.geocode", lambda _location: (None, None))
    client = TestClient(app)
    now = datetime(2030, 1, 1, 9, tzinfo=UTC)
    payload = {
        "role": "server",
        "location": "Bath",
        "start_time": (now + timedelta(hours=2)).isoformat(),
        "end_time": (now + timedelta(hours=6)).isoformat(),
        "pay_rate": "15.00",
        "now": now.isoformat(),
    }
    headers = {
        "X-Actor-Role": "operator",
        "X-Actor-Id": "idempotent-operator",
        "X-Account-Id": "idempotent-venue",
        "Idempotency-Key": "shift-retry-1",
    }
    if not use_in_memory_repositories():
        monkeypatch.setenv("OPERATOR_INVITE_CODES", INVITE_CODE)
        operator = _register_verified_operator(client, "idempotency@pg-test.example")
        headers = {**_auth(operator), "Idempotency-Key": "shift-retry-1"}

    first = client.post("/shifts", json=payload, headers=headers)
    replay = client.post("/shifts", json=payload, headers=headers)

    assert first.status_code == 200, first.text
    assert replay.status_code == 200, replay.text
    assert replay.json()["shift_id"] == first.json()["shift_id"]
    assert replay.headers["Idempotency-Replayed"] == "true"

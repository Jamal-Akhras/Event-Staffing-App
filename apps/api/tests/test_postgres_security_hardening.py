from __future__ import annotations

import threading
from datetime import timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select

from apps.api.src import main
from apps.api.src.datetime_utils import utc_now
from apps.api.src.db.idempotency_models import IdempotencyRecordModel
from apps.api.src.db.models import ShiftModel, UserModel, WorkerProfileModel
from apps.api.src.db.trust_models import ReportModel
from apps.api.src.services.idempotency import IdempotencyService
from apps.api.tests.test_postgres_flows import (
    INVITE_CODE,
    PASSWORD,
    _auth,
    _create_shift,
    _db_session,
    _register_verified_operator,
    _register_worker,
)

pytestmark = pytest.mark.postgres


@pytest.fixture()
def client(monkeypatch) -> TestClient:
    monkeypatch.setenv("OPERATOR_INVITE_CODES", INVITE_CODE)
    monkeypatch.setattr("apps.api.src.routes.shifts.geocode", lambda _location: (None, None))
    return TestClient(main.app)


def _verify_user(client: TestClient, user_id: str) -> None:
    with _db_session() as session:
        token = session.get(UserModel, user_id).email_verification_token
    response = client.post("/auth/verify-email", json={"token": token})
    assert response.status_code == 200, response.text


def test_account_export_and_deletion_persist_and_revoke_access(client: TestClient) -> None:
    email = "privacy-worker@pg-test.example"
    worker = _register_worker(client, email)

    exported = client.post(
        "/auth/account-export",
        json={"password": PASSWORD},
        headers=_auth(worker),
    )

    assert exported.status_code == 200, exported.text
    export_data = exported.json()["data"]
    assert export_data["account"]["email"] == email
    assert export_data["worker_profile"]["worker_id"] == worker["worker_profile_id"]
    assert "hashed_password" not in str(export_data)
    assert "email_verification_token" not in str(export_data)

    deleted = client.request(
        "DELETE",
        "/auth/account",
        json={"password": PASSWORD, "confirmation": "DELETE"},
        headers=_auth(worker),
    )
    old_session = client.get("/auth/me", headers=_auth(worker))

    assert deleted.status_code == 200, deleted.text
    assert old_session.status_code == 401
    with _db_session() as session:
        user = session.get(UserModel, worker["user_id"])
        profile = session.get(WorkerProfileModel, worker["worker_profile_id"])
        assert user.is_active is False
        assert user.email.startswith("deleted+")
        assert user.deactivated_at is not None
        assert profile.display_name == "Deleted user"
        assert profile.email is None

    replacement = _register_worker(client, email)
    assert replacement["user_id"] != worker["user_id"]


def test_report_persists_and_cross_venue_operator_is_denied(
    client: TestClient,
    monkeypatch,
) -> None:
    first = _register_verified_operator(client, "report-owner@pg-test.example")
    second = _register_verified_operator(client, "report-intruder@pg-test.example")
    worker = _register_worker(client, "report-worker@pg-test.example")
    _verify_user(client, worker["user_id"])
    shift = _create_shift(client, first)
    monkeypatch.setenv("DEV_MODE", "false")

    reported = client.post(
        "/reports",
        json={
            "subject_type": "venue",
            "subject_id": first["account_id"],
            "category": "safety",
            "description": "A safety issue that needs review.",
        },
        headers=_auth(worker),
    )
    denied = client.post(
        "/reports",
        json={
            "subject_type": "shift",
            "subject_id": shift["shift_id"],
            "category": "other",
            "description": "Trying to access another venue's shift.",
        },
        headers=_auth(second),
    )

    assert reported.status_code == 201, reported.text
    assert denied.status_code == 403
    with _db_session() as session:
        stored = session.get(ReportModel, reported.json()["report_id"])
        assert stored.reporter_user_id == worker["user_id"]
        assert session.get(ShiftModel, shift["shift_id"]).venue_id == first["account_id"]


def test_same_idempotency_key_is_serialized_across_connections(client: TestClient) -> None:
    worker = _register_worker(client, "idempotency-race@pg-test.example")
    barrier = threading.Barrier(2)
    outcomes: list[str] = []
    errors: list[BaseException] = []
    result_lock = threading.Lock()

    def attempt() -> None:
        from apps.api.src.db.database import SessionLocal

        try:
            with SessionLocal() as session, session.begin():
                barrier.wait(timeout=10)
                service = IdempotencyService(session)
                started = service.start(
                    worker["user_id"],
                    "security.test",
                    "same-key",
                    {"value": 1},
                )
                if started.cached_response is None:
                    service.finish(started.record_id, {"result": "same"})
                    outcome = "created"
                else:
                    outcome = "replayed"
            with result_lock:
                outcomes.append(outcome)
        except BaseException as exc:
            with result_lock:
                errors.append(exc)

    threads = [threading.Thread(target=attempt) for _ in range(2)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=30)

    assert all(not thread.is_alive() for thread in threads), "idempotency threads deadlocked"
    assert errors == []
    assert sorted(outcomes) == ["created", "replayed"]
    with _db_session() as session:
        count = session.scalar(select(func.count()).select_from(IdempotencyRecordModel))
        assert count == 1


def test_expired_idempotency_key_can_be_reused(client: TestClient) -> None:
    worker = _register_worker(client, "idempotency-expiry@pg-test.example")
    with _db_session() as session, session.begin():
        service = IdempotencyService(session)
        first = service.start(worker["user_id"], "security.test", "expired", {"value": 1})
        service.finish(first.record_id, {"result": "old"})
    with _db_session() as session, session.begin():
        row = session.get(IdempotencyRecordModel, first.record_id)
        row.expires_at = utc_now() - timedelta(seconds=1)
    with _db_session() as session, session.begin():
        service = IdempotencyService(session)
        replacement = service.start(
            worker["user_id"],
            "security.test",
            "expired",
            {"value": 2},
        )
        service.finish(replacement.record_id, {"result": "new"})

    assert replacement.cached_response is None
    assert replacement.record_id != first.record_id

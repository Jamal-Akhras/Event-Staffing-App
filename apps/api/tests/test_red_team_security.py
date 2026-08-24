from __future__ import annotations

from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient

import apps.api.src.auth.dependencies as auth_dependencies
from apps.api.src.auth.jwt import create_access_token
from apps.api.src.config import use_in_memory_repositories
from apps.api.src.main import app
from apps.api.tests.test_postgres_flows import (
    INVITE_CODE,
    _create_shift,
    _register_verified_operator,
)


def _register_worker(client: TestClient, email: str) -> dict:
    response = client.post(
        "/auth/register",
        json={"email": email, "password": "password123"},
    )
    assert response.status_code == 200, response.text
    return response.json()


def test_actor_headers_cannot_bypass_auth_when_dev_mode_is_disabled(monkeypatch) -> None:
    monkeypatch.setattr(auth_dependencies, "DEV_MODE", False)
    client = TestClient(app)

    response = client.get(
        "/auth/me",
        headers={"X-Actor-Role": "system", "X-Actor-Id": "attacker"},
    )

    assert response.status_code == 401


def test_jwt_role_and_tenant_claims_cannot_escalate_database_identity() -> None:
    client = TestClient(app)
    worker = _register_worker(client, "redteam-claims@example.com")
    forged_claims = create_access_token(
        {
            "user_id": worker["user_id"],
            "email": worker["email"],
            "role": "operator",
            "account_id": "victim-venue",
            "session_version": 0,
        }
    )

    session = client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {forged_claims}"},
    )
    create = client.post(
        "/shifts",
        json={
            "role": "server",
            "location": "Bath",
            "start_time": "2030-01-01T11:00:00Z",
            "end_time": "2030-01-01T15:00:00Z",
            "pay_rate": "15.00",
        },
        headers={"Authorization": f"Bearer {forged_claims}"},
    )

    assert session.status_code == 200
    assert session.json()["role"] == "worker"
    assert create.status_code == 403


def test_tampered_jwt_is_rejected() -> None:
    client = TestClient(app)
    worker = _register_worker(client, "redteam-tamper@example.com")
    header, payload, signature = worker["access_token"].split(".")
    replacement = "a" if payload[0] != "a" else "b"
    tampered = ".".join((header, replacement + payload[1:], signature))

    response = client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {tampered}"},
    )

    assert response.status_code == 401


def test_unverified_worker_cannot_apply_in_production_mode(monkeypatch) -> None:
    client = TestClient(app)
    now = datetime(2030, 1, 1, 9, tzinfo=UTC)
    if use_in_memory_repositories():
        shift = client.post(
            "/shifts",
            json={
                "role": "server",
                "location": "Bath",
                "start_time": (now + timedelta(hours=2)).isoformat(),
                "end_time": (now + timedelta(hours=6)).isoformat(),
                "pay_rate": "15.00",
                "now": now.isoformat(),
            },
            headers={
                "X-Actor-Role": "operator",
                "X-Actor-Id": "redteam-operator",
                "X-Account-Id": "redteam-venue",
            },
        ).json()
    else:
        monkeypatch.setenv("OPERATOR_INVITE_CODES", INVITE_CODE)
        operator = _register_verified_operator(client, "redteam-operator@pg-test.example")
        shift = _create_shift(client, operator)
    worker = _register_worker(client, "redteam-unverified@example.com")
    monkeypatch.setattr(auth_dependencies, "DEV_MODE", False)
    monkeypatch.setenv("DEV_MODE", "false")

    response = client.post(
        "/applications",
        json={"shift_id": shift["shift_id"], "worker_id": worker["worker_profile_id"]},
        headers={"Authorization": f"Bearer {worker['access_token']}"},
    )

    assert response.status_code == 403
    assert "verify" in response.json()["detail"].lower()


def test_account_deletion_requires_password_and_exact_confirmation() -> None:
    client = TestClient(app)
    worker = _register_worker(client, "redteam-delete@example.com")
    headers = {"Authorization": f"Bearer {worker['access_token']}"}

    wrong_password = client.request(
        "DELETE",
        "/auth/account",
        json={"password": "incorrect-password", "confirmation": "DELETE"},
        headers=headers,
    )
    wrong_confirmation = client.request(
        "DELETE",
        "/auth/account",
        json={"password": "password123", "confirmation": "yes"},
        headers=headers,
    )

    assert wrong_password.status_code == 403
    assert wrong_confirmation.status_code == 422


def test_oversized_inputs_and_unbounded_limits_are_rejected() -> None:
    client = TestClient(app)
    headers = {"X-Actor-Role": "operator", "X-Actor-Id": "redteam-limits"}

    oversized = client.post(
        "/shifts",
        json={
            "role": "x" * 121,
            "location": "Bath",
            "start_time": "2030-01-01T11:00:00Z",
            "end_time": "2030-01-01T15:00:00Z",
            "pay_rate": "15.00",
        },
        headers=headers,
    )
    abusive_limit = client.get("/shifts?limit=1000000", headers=headers)

    assert oversized.status_code == 422
    assert abusive_limit.status_code == 422

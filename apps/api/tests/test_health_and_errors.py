from __future__ import annotations

from fastapi.testclient import TestClient

from apps.api.src.config import use_in_memory_repositories
from apps.api.src.main import app

client = TestClient(app)


def test_liveness_and_development_readiness() -> None:
    live = client.get("/live")
    ready = client.get("/ready")

    assert live.status_code == 200
    assert ready.status_code == 200
    assert ready.json()["status"] == "ready"
    expected_database = "development_in_memory" if use_in_memory_repositories() else "ok"
    assert ready.json()["components"]["database"] == expected_database


def test_request_id_is_validated_and_security_headers_are_set() -> None:
    response = client.get("/health", headers={"X-Request-ID": "launch-check-123"})
    rejected = client.get("/health", headers={"X-Request-ID": "bad id with spaces"})

    assert response.headers["X-Request-ID"] == "launch-check-123"
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "DENY"
    assert response.headers["Permissions-Policy"] == "camera=(), microphone=(), geolocation=()"
    assert rejected.headers["X-Request-ID"] != "bad id with spaces"


def test_production_responses_enable_transport_security(monkeypatch) -> None:
    monkeypatch.setenv("ENVIRONMENT", "production")

    response = client.get("/health")

    assert response.headers["Strict-Transport-Security"].startswith("max-age=31536000")
    assert response.headers["Content-Security-Policy"] == "default-src 'none'; frame-ancestors 'none'"


def test_validation_errors_have_stable_machine_readable_shape() -> None:
    response = client.post(
        "/auth/register",
        json={"email": "not-an-email", "password": "short"},
    )

    assert response.status_code == 422
    payload = response.json()
    assert payload["error"]["code"] == "VALIDATION_ERROR"
    assert payload["error"]["message"] == "Request validation failed."
    assert payload["error"]["details"]


def test_http_errors_have_stable_machine_readable_shape() -> None:
    response = client.get("/auth/me")

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "AUTHENTICATION_REQUIRED"

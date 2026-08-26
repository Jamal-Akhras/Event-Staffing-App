from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from apps.api.src.deps import get_account_repo, get_organisation_repo, get_user_repo
from apps.api.src.main import app
from apps.api.src.repositories.in_memory_account_repository import InMemoryAccountRepository
from apps.api.src.repositories.in_memory_organisation_repository import InMemoryOrganisationRepository
from apps.api.src.repositories.in_memory_user_repository import InMemoryUserRepository

client = TestClient(app)

_VALID_CODE = "test-invite-code"


@pytest.fixture(autouse=True)
def configure_invite_codes(monkeypatch):
    monkeypatch.setenv("OPERATOR_INVITE_CODES", f"{_VALID_CODE},another-code")
    yield


@pytest.fixture(autouse=True)
def override_repos():
    user_repo = InMemoryUserRepository()
    account_repo = InMemoryAccountRepository()
    organisation_repo = InMemoryOrganisationRepository(account_repo)
    app.dependency_overrides[get_user_repo] = lambda: user_repo
    app.dependency_overrides[get_account_repo] = lambda: account_repo
    app.dependency_overrides[get_organisation_repo] = lambda: organisation_repo
    yield
    app.dependency_overrides.clear()
    user_repo.clear()


def _payload(invite_code: str | None) -> dict:
    body = {
        "email": "venue@example.com",
        "password": "password123",
        "venue_name": "Test Venue",
        "country": "GB",
        "market_id": "bath-gb",
    }
    if invite_code is not None:
        body["invite_code"] = invite_code
    return body


def test_operator_register_rejects_bad_invite_code():
    response = client.post("/auth/register/operator", json=_payload("wrong-code"))
    assert response.status_code == 403
    assert "invite code" in response.json()["detail"].lower()


def test_operator_register_requires_invite_code_field():
    response = client.post("/auth/register/operator", json=_payload(None))
    assert response.status_code == 422


def test_operator_register_accepts_valid_invite_code():
    response = client.post("/auth/register/operator", json=_payload(_VALID_CODE))
    assert response.status_code == 200
    data = response.json()
    assert data["role"] == "operator"
    assert data["email_verified"] is False

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from apps.api.src.auth.password import hash_password
from apps.api.src.deps import get_account_repo, get_organisation_repo, get_user_repo, get_worker_profile_repo
from apps.api.src.main import app
from apps.api.src.models.user import User
from apps.api.src.repositories.in_memory_account_repository import InMemoryAccountRepository
from apps.api.src.repositories.in_memory_organisation_repository import InMemoryOrganisationRepository
from apps.api.src.repositories.in_memory_user_repository import InMemoryUserRepository
from apps.api.src.repositories.in_memory_worker_profile_repository import InMemoryWorkerProfileRepository
from apps.api.src.services.clerk_identity import IdentityVerificationError, SsoIdentity
from apps.api.src.sso_dependencies import get_identity_verifier

client = TestClient(app)

VALID_TOKEN = "clerk-session-token-" + "x" * 24
INVITE_CODE = "sso-invite-code"


class FakeVerifier:
    def __init__(self, identity: SsoIdentity) -> None:
        self.identity = identity

    def verify(self, token: str) -> SsoIdentity:
        if token != VALID_TOKEN:
            raise IdentityVerificationError("Sign-in token was rejected.")
        return self.identity


def _identity(email: str = "priya@example.com", verified: bool = True) -> SsoIdentity:
    return SsoIdentity("clerk", "user_abc123", email, verified, "Priya Shah")


@pytest.fixture
def repos(monkeypatch):
    monkeypatch.setenv("OPERATOR_INVITE_CODES", INVITE_CODE)
    user_repo = InMemoryUserRepository()
    worker_repo = InMemoryWorkerProfileRepository()
    account_repo = InMemoryAccountRepository()
    organisation_repo = InMemoryOrganisationRepository(account_repo)
    app.dependency_overrides[get_user_repo] = lambda: user_repo
    app.dependency_overrides[get_worker_profile_repo] = lambda: worker_repo
    app.dependency_overrides[get_account_repo] = lambda: account_repo
    app.dependency_overrides[get_organisation_repo] = lambda: organisation_repo
    app.dependency_overrides[get_identity_verifier] = lambda: FakeVerifier(_identity())
    yield user_repo, worker_repo
    app.dependency_overrides.clear()
    user_repo.clear()
    worker_repo.clear()


def test_first_sso_sign_in_creates_a_verified_worker(repos):
    user_repo, worker_repo = repos

    response = client.post("/auth/sso", json={"token": VALID_TOKEN, "role": "worker"})

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["role"] == "worker"
    assert body["email_verified"] is True
    user = user_repo.get(body["user_id"])
    assert user.sso_provider == "clerk" and user.sso_subject == "user_abc123"
    profile = worker_repo.get(body["worker_profile_id"])
    assert profile.display_name == "Priya Shah"


def test_sso_links_an_existing_password_account_by_email(repos):
    user_repo, _ = repos
    now = datetime.now(UTC)
    existing = User(
        user_id=str(uuid4()),
        email="priya@example.com",
        hashed_password=hash_password("password123"),
        role="worker",
        account_id=None,
        worker_profile_id=str(uuid4()),
        is_active=True,
        created_at=now,
        updated_at=now,
        email_verified=False,
        email_verification_token="pending-token",
    )
    user_repo.save(existing)

    first = client.post("/auth/sso", json={"token": VALID_TOKEN, "role": "worker"})
    second = client.post("/auth/sso", json={"token": VALID_TOKEN, "role": "worker"})

    assert first.status_code == 200 and second.status_code == 200
    assert first.json()["user_id"] == existing.user_id == second.json()["user_id"]
    linked = user_repo.get(existing.user_id)
    assert linked.sso_subject == "user_abc123"
    assert linked.email_verified is True and linked.email_verification_token is None

    login = client.post("/auth/login", json={"email": "priya@example.com", "password": "password123"})
    assert login.status_code == 200


def test_operator_without_an_account_is_told_to_register(repos):
    response = client.post("/auth/sso", json={"token": VALID_TOKEN, "role": "operator"})

    assert response.status_code == 404
    assert response.json()["detail"] == {"code": "SSO_REGISTRATION_REQUIRED", "email": "priya@example.com"}


def test_operator_can_register_a_venue_with_an_sso_token(repos):
    user_repo, _ = repos

    registered = client.post(
        "/auth/register/operator",
        json={
            "email": "priya@example.com",
            "sso_token": VALID_TOKEN,
            "venue_name": "Harrow & Vine",
            "country": "GB",
            "market_id": "bath-gb",
            "invite_code": INVITE_CODE,
        },
    )

    assert registered.status_code == 200, registered.text
    body = registered.json()
    assert body["role"] == "operator" and body["email_verified"] is True and body["venue_id"]
    assert user_repo.get(body["user_id"]).sso_subject == "user_abc123"

    signed_in = client.post("/auth/sso", json={"token": VALID_TOKEN, "role": "operator"})
    assert signed_in.status_code == 200
    assert signed_in.json()["user_id"] == body["user_id"]


def test_operator_registration_rejects_mismatched_email_and_missing_credentials(repos):
    base = {"venue_name": "Harrow & Vine", "country": "GB", "market_id": "bath-gb", "invite_code": INVITE_CODE}

    mismatched = client.post("/auth/register/operator", json={**base, "email": "other@example.com", "sso_token": VALID_TOKEN})
    assert mismatched.status_code == 400

    neither = client.post("/auth/register/operator", json={**base, "email": "priya@example.com"})
    assert neither.status_code == 422

    both = client.post(
        "/auth/register/operator",
        json={**base, "email": "priya@example.com", "password": "password123", "sso_token": VALID_TOKEN},
    )
    assert both.status_code == 422


def test_bad_token_unverified_email_and_unconfigured_sso_are_rejected(repos):
    bad = client.post("/auth/sso", json={"token": "not-the-right-token-" + "y" * 20, "role": "worker"})
    assert bad.status_code == 401

    app.dependency_overrides[get_identity_verifier] = lambda: FakeVerifier(_identity(verified=False))
    unverified = client.post("/auth/sso", json={"token": VALID_TOKEN, "role": "worker"})
    assert unverified.status_code == 403

    app.dependency_overrides[get_identity_verifier] = lambda: None
    unconfigured = client.post("/auth/sso", json={"token": VALID_TOKEN, "role": "worker"})
    assert unconfigured.status_code == 503

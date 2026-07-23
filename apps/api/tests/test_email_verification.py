"""Tests for the email-verification flow and operator shift-create gating."""

from __future__ import annotations

from datetime import datetime

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from apps.api.src.auth.dependencies import ActorContext, ActorRole
from apps.api.src.deps import get_account_repo, get_user_repo, get_worker_profile_repo
from apps.api.src.main import app
from apps.api.src.models.user import User
from apps.api.src.repositories.in_memory_account_repository import InMemoryAccountRepository
from apps.api.src.repositories.in_memory_user_repository import InMemoryUserRepository
from apps.api.src.repositories.in_memory_worker_profile_repository import (
    InMemoryWorkerProfileRepository,
)
from apps.api.src.routes.shifts import _require_verified_operator

client = TestClient(app)


@pytest.fixture
def user_repo():
    repo = InMemoryUserRepository()
    yield repo
    repo.clear()


@pytest.fixture(autouse=True)
def override_repos(user_repo):
    worker_repo = InMemoryWorkerProfileRepository()
    account_repo = InMemoryAccountRepository()
    app.dependency_overrides[get_user_repo] = lambda: user_repo
    app.dependency_overrides[get_worker_profile_repo] = lambda: worker_repo
    app.dependency_overrides[get_account_repo] = lambda: account_repo
    yield
    app.dependency_overrides.clear()
    worker_repo.clear()


def test_worker_registers_unverified_with_token(user_repo):
    response = client.post(
        "/auth/register",
        json={"email": "verify-worker@example.com", "password": "password123"},
    )
    assert response.status_code == 200
    assert response.json()["email_verified"] is False

    stored = user_repo.get_by_email("verify-worker@example.com")
    assert stored.email_verified is False
    assert stored.email_verification_token


def test_verify_email_marks_verified(user_repo):
    client.post(
        "/auth/register",
        json={"email": "verify-flow@example.com", "password": "password123"},
    )
    token = user_repo.get_by_email("verify-flow@example.com").email_verification_token

    response = client.post("/auth/verify-email", json={"token": token})
    assert response.status_code == 200
    assert response.json()["email_verified"] is True

    stored = user_repo.get_by_email("verify-flow@example.com")
    assert stored.email_verified is True
    assert stored.email_verification_token is None


def test_verify_email_rejects_unknown_token():
    response = client.post("/auth/verify-email", json={"token": "does-not-exist"})
    assert response.status_code == 400


def test_resend_verification_issues_new_token(user_repo):
    client.post(
        "/auth/register",
        json={"email": "resend@example.com", "password": "password123"},
    )
    original = user_repo.get_by_email("resend@example.com").email_verification_token

    response = client.post("/auth/resend-verification", json={"email": "resend@example.com"})
    assert response.status_code == 200

    refreshed = user_repo.get_by_email("resend@example.com").email_verification_token
    assert refreshed
    assert refreshed != original


def test_resend_verification_unknown_email_is_opaque():
    response = client.post("/auth/resend-verification", json={"email": "nobody@example.com"})
    assert response.status_code == 200


def _operator_user(email_verified: bool) -> User:
    now = datetime.utcnow()
    return User(
        user_id="op-1",
        email="op@example.com",
        hashed_password="x",
        role="operator",
        account_id="acct-1",
        worker_profile_id=None,
        is_active=True,
        created_at=now,
        updated_at=now,
        email_verified=email_verified,
    )


def test_unverified_operator_cannot_create_shift(user_repo, monkeypatch):
    monkeypatch.setenv("DEV_MODE", "false")
    user_repo.save(_operator_user(email_verified=False))
    actor = ActorContext(user_id="op-1", role=ActorRole.OPERATOR, account_id="acct-1")

    with pytest.raises(HTTPException) as exc:
        _require_verified_operator(actor, user_repo)
    assert exc.value.status_code == 403


def test_verified_operator_can_create_shift(user_repo, monkeypatch):
    monkeypatch.setenv("DEV_MODE", "false")
    user_repo.save(_operator_user(email_verified=True))
    actor = ActorContext(user_id="op-1", role=ActorRole.OPERATOR, account_id="acct-1")

    _require_verified_operator(actor, user_repo)

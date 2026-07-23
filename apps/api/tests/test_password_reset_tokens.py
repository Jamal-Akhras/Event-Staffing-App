from __future__ import annotations

from datetime import datetime, timedelta
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

import apps.api.src.auth.jwt as jwt_module
from apps.api.src.auth.jwt import create_reset_token
from apps.api.src.auth.password import hash_password, verify_password
from apps.api.src.deps import get_user_repo
from apps.api.src.main import app
from apps.api.src.models.user import User
from apps.api.src.repositories.in_memory_user_repository import InMemoryUserRepository

client = TestClient(app)


@pytest.fixture
def user_repo():
    repo = InMemoryUserRepository()
    yield repo
    repo.clear()


@pytest.fixture(autouse=True)
def override_user_repo(user_repo):
    app.dependency_overrides[get_user_repo] = lambda: user_repo
    yield
    app.dependency_overrides.clear()


def test_reset_token_works_once(user_repo):
    user = _save_user(user_repo, "reset-once@example.com")
    token = create_reset_token(user.email)

    response = client.post(
        "/auth/reset-password",
        json={"token": token, "new_password": "newpassword123"},
    )

    assert response.status_code == 200
    updated = user_repo.get_by_email(user.email)
    assert updated is not None
    assert updated.password_changed_at is not None
    assert verify_password("newpassword123", updated.hashed_password)


def test_reset_token_rejected_after_use(user_repo):
    user = _save_user(user_repo, "single-use@example.com")
    token = create_reset_token(user.email)

    first_response = client.post(
        "/auth/reset-password",
        json={"token": token, "new_password": "firstpassword123"},
    )
    second_response = client.post(
        "/auth/reset-password",
        json={"token": token, "new_password": "secondpassword123"},
    )

    assert first_response.status_code == 200
    assert second_response.status_code == 400
    updated = user_repo.get_by_email(user.email)
    assert updated is not None
    assert verify_password("firstpassword123", updated.hashed_password)


def test_reset_token_expires_after_one_hour(user_repo, monkeypatch):
    user = _save_user(user_repo, "expired-reset@example.com")
    issued_at = datetime.utcnow() - timedelta(hours=1, seconds=1)

    class ExpiredDateTime(datetime):
        @classmethod
        def utcnow(cls) -> datetime:
            return issued_at

    monkeypatch.setattr(jwt_module, "datetime", ExpiredDateTime)
    token = jwt_module.create_reset_token(user.email)

    response = client.post(
        "/auth/reset-password",
        json={"token": token, "new_password": "newpassword123"},
    )

    assert response.status_code == 400
    updated = user_repo.get_by_email(user.email)
    assert updated is not None
    assert verify_password("oldpassword123", updated.hashed_password)
    assert updated.password_changed_at is None


def _save_user(repo: InMemoryUserRepository, email: str) -> User:
    now = datetime.utcnow()
    user = User(
        user_id=str(uuid4()),
        email=email,
        hashed_password=hash_password("oldpassword123"),
        role="worker",
        account_id=None,
        worker_profile_id=str(uuid4()),
        is_active=True,
        created_at=now,
        updated_at=now,
    )
    return repo.save(user)

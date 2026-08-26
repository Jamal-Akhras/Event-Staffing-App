from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from apps.api.src.auth.jwt import JWTError, create_access_token, decode_access_token, revoke_access_token
from apps.api.src.auth.token_denylist import get_token_denylist
from apps.api.src.deps import get_user_repo, get_worker_profile_repo
from apps.api.src.main import app
from apps.api.src.repositories.in_memory_user_repository import InMemoryUserRepository
from apps.api.src.repositories.in_memory_worker_profile_repository import (
    InMemoryWorkerProfileRepository,
)

client = TestClient(app)


@pytest.fixture
def user_repo():
    repo = InMemoryUserRepository()
    yield repo
    repo.clear()


@pytest.fixture(autouse=True)
def override_repos(user_repo):
    worker_repo = InMemoryWorkerProfileRepository()
    app.dependency_overrides[get_user_repo] = lambda: user_repo
    app.dependency_overrides[get_worker_profile_repo] = lambda: worker_repo
    yield
    app.dependency_overrides.clear()
    worker_repo.clear()


@pytest.fixture(autouse=True)
def clear_denylist():
    denylist = get_token_denylist()
    denylist.clear()
    yield
    denylist.clear()


def test_access_token_has_jti():
    token = create_access_token({"user_id": "u1", "email": "a@b.com", "role": "worker"})
    claims = decode_access_token(token)
    assert claims["jti"]


def test_decode_rejects_revoked_token():
    token = create_access_token({"user_id": "u1", "email": "a@b.com", "role": "worker"})
    assert decode_access_token(token)["user_id"] == "u1"

    revoke_access_token(token)

    with pytest.raises(JWTError):
        decode_access_token(token)


def test_logout_revokes_token():
    register = client.post(
        "/auth/register",
        json={"email": "logout-worker@example.com", "password": "password123"},
    )
    assert register.status_code == 200
    token = register.json()["access_token"]

    logout = client.post("/auth/logout", headers={"Authorization": f"Bearer {token}"})
    assert logout.status_code == 200
    assert "revoked" in logout.json()["message"].lower()

    with pytest.raises(JWTError):
        decode_access_token(token)


def test_logout_requires_token():
    response = client.post("/auth/logout")
    assert response.status_code == 401


def test_logout_all_revokes_every_session():
    register = client.post(
        "/auth/register",
        json={"email": "logout-all@example.com", "password": "password123"},
    )
    token = register.json()["access_token"]

    response = client.post(
        "/auth/logout-all",
        headers={"Authorization": f"Bearer {token}"},
    )
    session = client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert session.status_code == 401


def test_account_deletion_anonymizes_user_and_revokes_session(user_repo):
    register = client.post(
        "/auth/register",
        json={"email": "delete-me@example.com", "password": "password123"},
    )
    token = register.json()["access_token"]
    user_id = register.json()["user_id"]

    response = client.request(
        "DELETE",
        "/auth/account",
        json={"password": "password123", "confirmation": "DELETE"},
        headers={"Authorization": f"Bearer {token}"},
    )
    session = client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200, response.text
    assert session.status_code == 401
    deleted = user_repo.get(user_id)
    assert deleted is not None
    assert deleted.is_active is False
    assert deleted.email == f"deleted+{user_id}@deleted.invalid"
    assert user_repo.get_by_email("delete-me@example.com") is None

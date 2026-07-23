"""Tests for authentication endpoints."""

from datetime import datetime
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from apps.api.src.main import app
from apps.api.src.auth.password import hash_password
from apps.api.src.models.user import User
from apps.api.src.deps import get_user_repo, get_worker_profile_repo
from apps.api.src.repositories.in_memory_user_repository import InMemoryUserRepository
from apps.api.src.repositories.in_memory_worker_profile_repository import InMemoryWorkerProfileRepository

client = TestClient(app)


@pytest.fixture
def user_repo():
    """Provide a fresh in-memory user repository for each test."""
    repo = InMemoryUserRepository()
    yield repo
    repo.clear()


@pytest.fixture
def worker_profile_repo():
    repo = InMemoryWorkerProfileRepository()
    yield repo
    repo.clear()


@pytest.fixture(autouse=True)
def override_repos(user_repo, worker_profile_repo):
    """Override the user repository dependency for all tests."""
    app.dependency_overrides[get_user_repo] = lambda: user_repo
    app.dependency_overrides[get_worker_profile_repo] = lambda: worker_profile_repo
    yield
    app.dependency_overrides.clear()


def test_register_worker_success(user_repo):
    """Test successful worker registration."""
    response = client.post(
        "/auth/register",
        json={"email": "worker@example.com", "password": "password123"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["token_type"] == "bearer"
    assert data["email"] == "worker@example.com"
    assert data["role"] == "worker"
    assert "access_token" in data
    assert "user_id" in data

    # Verify user was created
    user = user_repo.get_by_email("worker@example.com")
    assert user is not None
    assert user.role == "worker"
    assert user.is_active is True


def test_register_duplicate_email(user_repo):
    """Test registration with an already registered email."""
    # Create existing user
    now = datetime.utcnow()
    existing_user = User(
        user_id=str(uuid4()),
        email="existing@example.com",
        hashed_password=hash_password("password123"),
        role="worker",
        account_id=None,
        worker_profile_id=str(uuid4()),
        is_active=True,
        created_at=now,
        updated_at=now,
    )
    user_repo.save(existing_user)

    # Try to register with same email
    response = client.post(
        "/auth/register",
        json={"email": "existing@example.com", "password": "newpassword"},
    )

    assert response.status_code == 400
    assert "already registered" in response.json()["detail"].lower()


def test_short_password_rejection():
    register_response = client.post(
        "/auth/register",
        json={"email": "short-worker@example.com", "password": "short"},
    )
    operator_response = client.post(
        "/auth/register/operator",
        json={
            "email": "short-operator@example.com",
            "password": "short",
            "venue_name": "Short Venue",
            "country": "GB",
        },
    )
    reset_response = client.post(
        "/auth/reset-password",
        json={"token": "invalid-token", "new_password": "short"},
    )

    assert register_response.status_code == 422
    assert operator_response.status_code == 422
    assert reset_response.status_code == 422


def test_login_success(user_repo):
    """Test successful login."""
    # Create a user
    now = datetime.utcnow()
    user = User(
        user_id=str(uuid4()),
        email="user@example.com",
        hashed_password=hash_password("correctpassword"),
        role="worker",
        account_id=None,
        worker_profile_id=str(uuid4()),
        is_active=True,
        created_at=now,
        updated_at=now,
    )
    user_repo.save(user)

    # Login
    response = client.post(
        "/auth/login",
        json={"email": "user@example.com", "password": "correctpassword"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["token_type"] == "bearer"
    assert data["email"] == "user@example.com"
    assert data["role"] == "worker"
    assert "access_token" in data


def test_login_rate_limit_response():
    for _ in range(5):
        response = client.post(
            "/auth/login",
            json={"email": "limited@example.com", "password": "password123"},
        )
        assert response.status_code == 401

    response = client.post(
        "/auth/login",
        json={"email": "limited@example.com", "password": "password123"},
    )

    assert response.status_code == 429


def test_login_invalid_email(user_repo):
    """Test login with non-existent email."""
    response = client.post(
        "/auth/login",
        json={"email": "nonexistent@example.com", "password": "password123"},
    )

    assert response.status_code == 401
    assert "invalid" in response.json()["detail"].lower()


def test_login_invalid_password(user_repo):
    """Test login with incorrect password."""
    # Create a user
    now = datetime.utcnow()
    user = User(
        user_id=str(uuid4()),
        email="user@example.com",
        hashed_password=hash_password("correctpassword"),
        role="worker",
        account_id=None,
        worker_profile_id=str(uuid4()),
        is_active=True,
        created_at=now,
        updated_at=now,
    )
    user_repo.save(user)

    # Try to login with wrong password
    response = client.post(
        "/auth/login",
        json={"email": "user@example.com", "password": "wrongpassword"},
    )

    assert response.status_code == 401
    assert "invalid" in response.json()["detail"].lower()


def test_login_inactive_user(user_repo):
    """Test login with an inactive user account."""
    # Create an inactive user
    now = datetime.utcnow()
    user = User(
        user_id=str(uuid4()),
        email="inactive@example.com",
        hashed_password=hash_password("password123"),
        role="worker",
        account_id=None,
        worker_profile_id=str(uuid4()),
        is_active=False,
        created_at=now,
        updated_at=now,
    )
    user_repo.save(user)

    # Try to login
    response = client.post(
        "/auth/login",
        json={"email": "inactive@example.com", "password": "password123"},
    )

    assert response.status_code == 401
    assert "inactive" in response.json()["detail"].lower()

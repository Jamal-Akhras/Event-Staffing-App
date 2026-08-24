from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

import apps.api.src.auth.jwt as jwt_module
from apps.api.src.auth.jwt import create_access_token, create_reset_token
from apps.api.src.auth.password import hash_password, verify_password
from apps.api.src.deps import get_outbox_publisher, get_user_repo
from apps.api.src.main import app
from apps.api.src.models.user import User
from apps.api.src.repositories.in_memory_user_repository import InMemoryUserRepository
from apps.api.src.repositories.in_memory_notification_repository import InMemoryNotificationRepository
from apps.api.src.services.email import Email
from apps.api.src.services.outbox_publisher import InMemoryOutboxPublisher

client = TestClient(app)


class RecordingTransport:
    def __init__(self) -> None:
        self.sent: list[Email] = []

    def send(self, email: Email) -> None:
        self.sent.append(email)


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
    assert updated.session_version == 1
    assert verify_password("newpassword123", updated.hashed_password)


def test_password_reset_revokes_existing_sessions(user_repo):
    user = _save_user(user_repo, "revoke-sessions@example.com")
    access_token = create_access_token(
        {
            "user_id": user.user_id,
            "email": user.email,
            "role": user.role,
            "session_version": user.session_version,
        }
    )
    reset_token = create_reset_token(user.email)

    reset = client.post(
        "/auth/reset-password",
        json={"token": reset_token, "new_password": "newpassword123"},
    )
    session = client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {access_token}"},
    )

    assert reset.status_code == 200
    assert session.status_code == 401


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
    issued_at = datetime.now(UTC) - timedelta(hours=1, seconds=1)

    class ExpiredDateTime(datetime):
        @classmethod
        def now(cls, tz=None) -> datetime:
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


def test_forgot_password_emails_working_reset_link(user_repo):
    transport = RecordingTransport()
    app.dependency_overrides[get_outbox_publisher] = lambda: InMemoryOutboxPublisher(
        InMemoryNotificationRepository(), transport
    )
    user = _save_user(user_repo, "email-link@example.com")

    response = client.post("/auth/forgot-password", json={"email": user.email})

    assert response.status_code == 200
    assert len(transport.sent) == 1
    email = transport.sent[0]
    assert email.to_address == user.email
    assert "/reset-password?token=" in email.body

    token = email.body.split("/reset-password?token=", 1)[1].split("\n", 1)[0].strip()
    reset = client.post(
        "/auth/reset-password",
        json={"token": token, "new_password": "newpassword123"},
    )
    assert reset.status_code == 200
    updated = user_repo.get_by_email(user.email)
    assert verify_password("newpassword123", updated.hashed_password)


def test_forgot_password_unknown_email_sends_nothing_with_identical_response(user_repo):
    transport = RecordingTransport()
    publisher = InMemoryOutboxPublisher(InMemoryNotificationRepository(), transport)
    app.dependency_overrides[get_outbox_publisher] = lambda: publisher
    user = _save_user(user_repo, "known-user@example.com")

    known = client.post("/auth/forgot-password", json={"email": user.email})
    unknown = client.post("/auth/forgot-password", json={"email": "nobody@example.com"})

    assert known.status_code == 200
    assert unknown.status_code == 200
    assert known.json()["message"] == unknown.json()["message"]
    assert len(transport.sent) == 1
    assert transport.sent[0].to_address == user.email


def _save_user(repo: InMemoryUserRepository, email: str) -> User:
    now = datetime.now(UTC)
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

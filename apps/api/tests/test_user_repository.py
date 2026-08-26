from datetime import UTC, datetime
from uuid import uuid4

from apps.api.src.models.user import User
from apps.api.src.repositories.in_memory_user_repository import InMemoryUserRepository


def test_in_memory_user_repository_save_and_get():
    repo = InMemoryUserRepository()
    now = datetime.now(UTC)

    user = User(
        user_id="user-1",
        email="test@example.com",
        hashed_password="hashed_password",
        role="worker",
        account_id=None,
        worker_profile_id="worker-1",
        is_active=True,
        created_at=now,
        updated_at=now,
    )

    saved_user = repo.save(user)
    assert saved_user.user_id == "user-1"

    retrieved = repo.get("user-1")
    assert retrieved is not None
    assert retrieved.user_id == "user-1"
    assert retrieved.email == "test@example.com"
    assert retrieved.role == "worker"


def test_in_memory_user_repository_get_by_email():
    repo = InMemoryUserRepository()
    now = datetime.now(UTC)

    user = User(
        user_id="user-1",
        email="test@example.com",
        hashed_password="hashed_password",
        role="worker",
        account_id=None,
        worker_profile_id="worker-1",
        is_active=True,
        created_at=now,
        updated_at=now,
    )
    repo.save(user)

    retrieved = repo.get_by_email("test@example.com")
    assert retrieved is not None
    assert retrieved.user_id == "user-1"
    assert retrieved.email == "test@example.com"


def test_in_memory_user_repository_get_by_email_case_insensitive():
    repo = InMemoryUserRepository()
    now = datetime.now(UTC)

    user = User(
        user_id="user-1",
        email="Test@Example.com",
        hashed_password="hashed_password",
        role="worker",
        account_id=None,
        worker_profile_id="worker-1",
        is_active=True,
        created_at=now,
        updated_at=now,
    )
    repo.save(user)

    retrieved = repo.get_by_email("test@example.com")
    assert retrieved is not None
    assert retrieved.user_id == "user-1"


def test_in_memory_user_repository_get_nonexistent():
    repo = InMemoryUserRepository()

    result = repo.get("nonexistent")
    assert result is None

    result = repo.get_by_email("nonexistent@example.com")
    assert result is None


def test_in_memory_user_repository_update():
    repo = InMemoryUserRepository()
    now = datetime.now(UTC)

    user = User(
        user_id="user-1",
        email="test@example.com",
        hashed_password="hashed_password",
        role="worker",
        account_id=None,
        worker_profile_id="worker-1",
        is_active=True,
        created_at=now,
        updated_at=now,
    )
    repo.save(user)

    updated_user = User(
        user_id="user-1",
        email="test@example.com",
        hashed_password="hashed_password",
        role="worker",
        account_id=None,
        worker_profile_id="worker-1",
        is_active=False,
        created_at=now,
        updated_at=datetime.now(UTC),
    )
    repo.save(updated_user)

    retrieved = repo.get("user-1")
    assert retrieved is not None
    assert retrieved.is_active is False


def test_in_memory_user_repository_clear():
    repo = InMemoryUserRepository()
    now = datetime.now(UTC)

    for i in range(3):
        user = User(
            user_id=f"user-{i}",
            email=f"user{i}@example.com",
            hashed_password="hashed_password",
            role="worker",
            account_id=None,
            worker_profile_id=f"worker-{i}",
            is_active=True,
            created_at=now,
            updated_at=now,
        )
        repo.save(user)

    repo.clear()

    assert repo.get("user-0") is None
    assert repo.get_by_email("user0@example.com") is None

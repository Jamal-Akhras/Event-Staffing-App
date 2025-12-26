"""Tests for User repository implementations."""

from datetime import datetime
from uuid import uuid4

from apps.api.src.models.user import User
from apps.api.src.repositories.in_memory_user_repository import InMemoryUserRepository


def test_in_memory_user_repository_save_and_get():
    """Test saving and retrieving a user."""
    repo = InMemoryUserRepository()
    now = datetime.utcnow()

    user = User(
        user_id="user-1",
        email="test@example.com",
        hashed_password="hashed_password",
        role="worker",
        worker_profile_id="worker-1",
        is_active=True,
        created_at=now,
        updated_at=now,
    )

    # Save user
    saved_user = repo.save(user)
    assert saved_user.user_id == "user-1"

    # Get by ID
    retrieved = repo.get("user-1")
    assert retrieved is not None
    assert retrieved.user_id == "user-1"
    assert retrieved.email == "test@example.com"
    assert retrieved.role == "worker"


def test_in_memory_user_repository_get_by_email():
    """Test retrieving a user by email address."""
    repo = InMemoryUserRepository()
    now = datetime.utcnow()

    user = User(
        user_id="user-1",
        email="test@example.com",
        hashed_password="hashed_password",
        role="worker",
        worker_profile_id="worker-1",
        is_active=True,
        created_at=now,
        updated_at=now,
    )

    repo.save(user)

    # Get by email
    retrieved = repo.get_by_email("test@example.com")
    assert retrieved is not None
    assert retrieved.user_id == "user-1"
    assert retrieved.email == "test@example.com"


def test_in_memory_user_repository_get_by_email_case_insensitive():
    """Test that email lookup is case-insensitive."""
    repo = InMemoryUserRepository()
    now = datetime.utcnow()

    user = User(
        user_id="user-1",
        email="Test@Example.com",
        hashed_password="hashed_password",
        role="worker",
        worker_profile_id="worker-1",
        is_active=True,
        created_at=now,
        updated_at=now,
    )

    repo.save(user)

    # Get by email with different case
    retrieved = repo.get_by_email("test@example.com")
    assert retrieved is not None
    assert retrieved.user_id == "user-1"


def test_in_memory_user_repository_get_nonexistent():
    """Test retrieving a user that doesn't exist."""
    repo = InMemoryUserRepository()

    # Get non-existent user by ID
    result = repo.get("nonexistent")
    assert result is None

    # Get non-existent user by email
    result = repo.get_by_email("nonexistent@example.com")
    assert result is None


def test_in_memory_user_repository_update():
    """Test updating an existing user."""
    repo = InMemoryUserRepository()
    now = datetime.utcnow()

    # Create initial user
    user = User(
        user_id="user-1",
        email="test@example.com",
        hashed_password="hashed_password",
        role="worker",
        worker_profile_id="worker-1",
        is_active=True,
        created_at=now,
        updated_at=now,
    )
    repo.save(user)

    # Update user (e.g., deactivate)
    updated_user = User(
        user_id="user-1",
        email="test@example.com",
        hashed_password="hashed_password",
        role="worker",
        worker_profile_id="worker-1",
        is_active=False,
        created_at=now,
        updated_at=datetime.utcnow(),
    )
    repo.save(updated_user)

    # Verify update
    retrieved = repo.get("user-1")
    assert retrieved is not None
    assert retrieved.is_active is False


def test_in_memory_user_repository_clear():
    """Test clearing all users from the repository."""
    repo = InMemoryUserRepository()
    now = datetime.utcnow()

    # Add some users
    for i in range(3):
        user = User(
            user_id=f"user-{i}",
            email=f"user{i}@example.com",
            hashed_password="hashed_password",
            role="worker",
            worker_profile_id=f"worker-{i}",
            is_active=True,
            created_at=now,
            updated_at=now,
        )
        repo.save(user)

    # Clear repository
    repo.clear()

    # Verify all users are gone
    assert repo.get("user-0") is None
    assert repo.get_by_email("user0@example.com") is None

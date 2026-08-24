from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime
from decimal import Decimal
from io import BytesIO

import pytest
from fastapi.testclient import TestClient
from PIL import Image

from apps.api.src.deps import get_account_repo, get_worker_profile_repo
from apps.api.src.main import app
from apps.api.src.models.account import Account
from apps.api.src.models.worker_profile import WorkerProfile
from apps.api.src.storage.object_storage import StoredObject
from apps.api.src.storage_dependencies import get_object_storage


def _image_bytes(image_format: str, size: tuple[int, int] = (8, 8)) -> bytes:
    buffer = BytesIO()
    Image.new("RGB", size, (200, 40, 40)).save(buffer, format=image_format)
    return buffer.getvalue()


PNG_BYTES = _image_bytes("PNG")
JPEG_BYTES = _image_bytes("JPEG")
WORKER_HEADERS = {"X-Actor-Role": "worker", "X-Actor-Id": "worker-1"}
OPERATOR_HEADERS = {
    "X-Actor-Role": "operator",
    "X-Actor-Id": "operator-1",
    "X-Account-Id": "venue-1",
}


class FakeStorage:
    def __init__(self) -> None:
        self.objects: dict[str, bytes] = {}
        self.content_types: dict[str, str] = {}
        self.deleted: list[str] = []

    def put(self, key: str, data: bytes, content_type: str) -> StoredObject:
        self.objects[key] = data
        self.content_types[key] = content_type
        return StoredObject(key, f"https://media.test/{key}")

    def delete(self, key: str) -> None:
        self.deleted.append(key)
        self.objects.pop(key, None)

    def key_from_url(self, url: str) -> str | None:
        prefix = "https://media.test/"
        return url.removeprefix(prefix) if url.startswith(prefix) else None


class FakeWorkerRepository:
    def __init__(self, profile: WorkerProfile) -> None:
        self.profile = profile

    def get(self, worker_id: str) -> WorkerProfile | None:
        return self.profile if self.profile.worker_id == worker_id else None

    def save(self, profile: WorkerProfile) -> WorkerProfile:
        self.profile = profile
        return profile


class FakeAccountRepository:
    def __init__(self, account: Account) -> None:
        self.account = account
        self.fail_save = False

    def get(self, account_id: str) -> Account | None:
        return self.account if self.account.account_id == account_id else None

    def save(self, account: Account) -> Account:
        if self.fail_save:
            raise RuntimeError("forced account save failure")
        self.account = account
        return account


@pytest.fixture()
def upload_dependencies():
    now = datetime(2030, 1, 1, tzinfo=UTC)
    worker_repo = FakeWorkerRepository(
        WorkerProfile(
            worker_id="worker-1",
            display_name="Worker One",
            role="Bartender",
            city="Bath",
            experience_years=2,
            reliability_score=100,
            badges=[],
            bio=None,
            languages=["English"],
            email="worker@example.com",
            phone=None,
            address=None,
            emergency_contact=None,
            pay_rate=Decimal("14.00"),
            notes=None,
            updated_at=now,
            avatar_url="https://media.test/workers/worker-1/avatars/old.png",
            market_id="bath-gb",
        )
    )
    account_repo = FakeAccountRepository(
        Account(
            account_id="venue-1",
            name="Bath Venue",
            country="GB",
            currency="GBP",
            created_at=now,
            avatar_url="https://media.test/venues/venue-1/avatars/old.png",
        )
    )
    storage = FakeStorage()
    app.dependency_overrides[get_worker_profile_repo] = lambda: worker_repo
    app.dependency_overrides[get_account_repo] = lambda: account_repo
    app.dependency_overrides[get_object_storage] = lambda: storage
    return worker_repo, account_repo, storage


def test_worker_avatar_upload_updates_profile_and_retires_previous_object(
    upload_dependencies,
) -> None:
    worker_repo, _, storage = upload_dependencies

    response = TestClient(app).post(
        "/uploads/avatar",
        headers=WORKER_HEADERS,
        files={"file": ("avatar.png", PNG_BYTES, "image/png")},
    )

    assert response.status_code == 200, response.text
    assert worker_repo.profile.avatar_url == response.json()["url"]
    assert list(storage.content_types.values()) == ["image/png"]
    assert storage.deleted == ["workers/worker-1/avatars/old.png"]


def test_venue_photo_upload_appends_public_object_url(upload_dependencies) -> None:
    _, account_repo, storage = upload_dependencies

    response = TestClient(app).post(
        "/uploads/venue-photo",
        headers=OPERATOR_HEADERS,
        files={"file": ("room.jpg", JPEG_BYTES, "image/jpeg")},
    )

    assert response.status_code == 200, response.text
    assert account_repo.account.photos == [response.json()["url"]]
    assert list(storage.content_types.values()) == ["image/jpeg"]


def test_upload_rejects_extension_content_mismatch(upload_dependencies) -> None:
    _, _, storage = upload_dependencies

    response = TestClient(app).post(
        "/uploads/venue-photo",
        headers=OPERATOR_HEADERS,
        files={"file": ("not-really-png.png", JPEG_BYTES, "image/png")},
    )

    assert response.status_code == 400
    assert storage.objects == {}


def test_failed_database_write_removes_new_object(upload_dependencies) -> None:
    _, account_repo, storage = upload_dependencies
    account_repo.fail_save = True

    response = TestClient(app, raise_server_exceptions=False).post(
        "/uploads/venue-avatar",
        headers=OPERATOR_HEADERS,
        files={"file": ("avatar.png", PNG_BYTES, "image/png")},
    )

    assert response.status_code == 500
    assert len(storage.deleted) == 1
    assert storage.objects == {}


def test_removing_venue_photo_retires_object_after_account_commit(upload_dependencies) -> None:
    _, account_repo, storage = upload_dependencies
    photo_url = "https://media.test/venues/venue-1/photos/old.png"
    account_repo.account = replace(account_repo.account, photos=[photo_url])

    response = TestClient(app).put(
        "/venues/me",
        headers=OPERATOR_HEADERS,
        json={"photos": []},
    )

    assert response.status_code == 200, response.text
    assert response.json()["photos"] == []
    assert storage.deleted == ["venues/venue-1/photos/old.png"]


def test_account_update_cannot_attach_or_delete_another_venues_media(
    upload_dependencies,
) -> None:
    _, account_repo, storage = upload_dependencies
    own_photo = "https://media.test/venues/venue-1/photos/own.png"
    victim_photo = "https://media.test/venues/venue-2/photos/victim.png"
    account_repo.account = replace(account_repo.account, photos=[own_photo])

    injection = TestClient(app).put(
        "/venues/me",
        headers=OPERATOR_HEADERS,
        json={"photos": [own_photo, victim_photo]},
    )

    assert injection.status_code == 400
    assert account_repo.account.photos == [own_photo]
    assert storage.deleted == []


def test_account_update_cannot_replace_avatar_url_directly(upload_dependencies) -> None:
    _, account_repo, storage = upload_dependencies
    original_avatar = account_repo.account.avatar_url

    response = TestClient(app).put(
        "/venues/me",
        headers=OPERATOR_HEADERS,
        json={"avatar_url": "https://media.test/venues/venue-2/avatars/victim.png"},
    )

    assert response.status_code == 422
    assert account_repo.account.avatar_url == original_avatar
    assert storage.deleted == []


def test_legacy_foreign_photo_is_not_deleted_by_venue_update(upload_dependencies) -> None:
    _, account_repo, storage = upload_dependencies
    victim_photo = "https://media.test/venues/venue-2/photos/victim.png"
    account_repo.account = replace(account_repo.account, photos=[victim_photo])

    response = TestClient(app).put(
        "/venues/me",
        headers=OPERATOR_HEADERS,
        json={"photos": []},
    )

    assert response.status_code == 200
    assert storage.deleted == []

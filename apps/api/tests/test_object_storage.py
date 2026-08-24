from __future__ import annotations

from pathlib import Path

import pytest

from apps.api.src.storage.local_object_storage import LocalObjectStorage
from apps.api.src.storage.s3_object_storage import S3ObjectStorage


class FakeS3Client:
    def __init__(self) -> None:
        self.put_calls: list[dict] = []
        self.delete_calls: list[dict] = []

    def put_object(self, **kwargs) -> None:
        self.put_calls.append(kwargs)

    def delete_object(self, **kwargs) -> None:
        self.delete_calls.append(kwargs)


def test_local_storage_writes_resolves_and_deletes_object(tmp_path: Path) -> None:
    storage = LocalObjectStorage(tmp_path)

    stored = storage.put("venues/one/photo.png", b"image", "image/png")

    assert stored.url == "/uploads/venues/one/photo.png"
    assert (tmp_path / stored.key).read_bytes() == b"image"
    assert storage.key_from_url(stored.url) == stored.key

    storage.delete(stored.key)
    assert not (tmp_path / stored.key).exists()


def test_local_storage_rejects_keys_outside_root(tmp_path: Path) -> None:
    storage = LocalObjectStorage(tmp_path)

    with pytest.raises(ValueError, match="escapes"):
        storage.put("../secret.txt", b"nope", "text/plain")


def test_s3_storage_sets_public_cache_metadata_and_builds_url() -> None:
    client = FakeS3Client()
    storage = S3ObjectStorage(client, "staffing-media", "https://media.example.com/assets")

    stored = storage.put("venues/one/my photo.png", b"image", "image/png")

    assert stored.url == "https://media.example.com/assets/venues/one/my%20photo.png"
    assert client.put_calls == [
        {
            "Bucket": "staffing-media",
            "Key": stored.key,
            "Body": b"image",
            "ContentType": "image/png",
            "CacheControl": "public, max-age=31536000, immutable",
        }
    ]
    assert storage.key_from_url(stored.url) == stored.key
    assert storage.key_from_url("https://other.example.com/assets/venues/one.png") is None
    assert storage.key_from_url("https://media.example.com/assets/venues/../secret") is None
    assert storage.key_from_url("https://media.example.com/assets/venues/%2E%2E/secret") is None
    assert storage.key_from_url("https://media.example.com/assets/venues%5Csecret") is None

    storage.delete(stored.key)
    assert client.delete_calls == [{"Bucket": "staffing-media", "Key": stored.key}]

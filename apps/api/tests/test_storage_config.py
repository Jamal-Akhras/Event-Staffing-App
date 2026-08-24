from __future__ import annotations

import pytest

from apps.api.src.storage.config import get_storage_settings

_S3_ENV_NAMES = (
    "OBJECT_STORAGE_BUCKET",
    "OBJECT_STORAGE_ENDPOINT_URL",
    "OBJECT_STORAGE_REGION",
    "OBJECT_STORAGE_ACCESS_KEY_ID",
    "OBJECT_STORAGE_SECRET_ACCESS_KEY",
    "OBJECT_STORAGE_PUBLIC_BASE_URL",
)


def test_local_storage_is_allowed_in_development(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("ENVIRONMENT", "development")
    monkeypatch.setenv("STORAGE_BACKEND", "local")
    monkeypatch.setenv("LOCAL_UPLOAD_DIRECTORY", str(tmp_path))

    settings = get_storage_settings()

    assert settings.backend == "local"
    assert settings.local_directory == tmp_path


def test_local_storage_is_rejected_outside_development(monkeypatch) -> None:
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.setenv("STORAGE_BACKEND", "local")

    with pytest.raises(RuntimeError, match="must be 's3'"):
        get_storage_settings()


def test_s3_storage_requires_complete_configuration(monkeypatch) -> None:
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.setenv("STORAGE_BACKEND", "s3")
    for name in _S3_ENV_NAMES:
        monkeypatch.delenv(name, raising=False)

    with pytest.raises(RuntimeError, match="OBJECT_STORAGE_BUCKET"):
        get_storage_settings()


def test_s3_storage_configuration_is_provider_portable(monkeypatch) -> None:
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.setenv("STORAGE_BACKEND", "s3")
    monkeypatch.setenv("OBJECT_STORAGE_BUCKET", "media")
    monkeypatch.setenv("OBJECT_STORAGE_ENDPOINT_URL", "https://r2.example.com")
    monkeypatch.setenv("OBJECT_STORAGE_REGION", "auto")
    monkeypatch.setenv("OBJECT_STORAGE_ACCESS_KEY_ID", "access")
    monkeypatch.setenv("OBJECT_STORAGE_SECRET_ACCESS_KEY", "secret")
    monkeypatch.setenv("OBJECT_STORAGE_PUBLIC_BASE_URL", "https://media.example.com")

    settings = get_storage_settings()

    assert settings.backend == "s3"
    assert settings.bucket == "media"
    assert settings.endpoint_url == "https://r2.example.com"
    assert settings.public_base_url == "https://media.example.com"

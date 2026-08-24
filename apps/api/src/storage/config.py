from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from apps.api.src.config import PROJECT_ROOT, get_env, get_environment


@dataclass(frozen=True)
class StorageSettings:
    backend: str
    local_directory: Path
    bucket: str = ""
    endpoint_url: str = ""
    region: str = ""
    access_key_id: str = ""
    secret_access_key: str = ""
    public_base_url: str = ""


def get_storage_settings() -> StorageSettings:
    backend = get_env("STORAGE_BACKEND", "local").strip().lower()
    if backend not in {"local", "s3"}:
        raise RuntimeError("STORAGE_BACKEND must be either 'local' or 's3'.")
    local_directory = _local_directory()
    if backend == "local":
        if get_environment() != "development":
            raise RuntimeError("STORAGE_BACKEND must be 's3' outside development.")
        return StorageSettings(backend=backend, local_directory=local_directory)

    values = {
        "bucket": get_env("OBJECT_STORAGE_BUCKET").strip(),
        "access_key_id": get_env("OBJECT_STORAGE_ACCESS_KEY_ID").strip(),
        "secret_access_key": get_env("OBJECT_STORAGE_SECRET_ACCESS_KEY").strip(),
        "public_base_url": get_env("OBJECT_STORAGE_PUBLIC_BASE_URL").strip(),
    }
    missing = [name for name, value in values.items() if not value]
    if missing:
        names = ", ".join(f"OBJECT_STORAGE_{name.upper()}" for name in missing)
        raise RuntimeError(f"S3 object storage is missing required settings: {names}.")
    if not values["public_base_url"].startswith(("https://", "http://")):
        raise RuntimeError("OBJECT_STORAGE_PUBLIC_BASE_URL must be an absolute HTTP(S) URL.")
    if get_environment() != "development" and not values["public_base_url"].startswith("https://"):
        raise RuntimeError("OBJECT_STORAGE_PUBLIC_BASE_URL must use HTTPS outside development.")
    return StorageSettings(
        backend=backend,
        local_directory=local_directory,
        bucket=values["bucket"],
        endpoint_url=get_env("OBJECT_STORAGE_ENDPOINT_URL").strip(),
        region=get_env("OBJECT_STORAGE_REGION", "auto").strip(),
        access_key_id=values["access_key_id"],
        secret_access_key=values["secret_access_key"],
        public_base_url=values["public_base_url"],
    )


def _local_directory() -> Path:
    configured = get_env("LOCAL_UPLOAD_DIRECTORY").strip()
    if configured:
        path = Path(configured)
        return path if path.is_absolute() else (PROJECT_ROOT / path).resolve()
    return (PROJECT_ROOT / "apps" / "api" / "uploads").resolve()

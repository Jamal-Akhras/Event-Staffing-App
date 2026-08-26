from __future__ import annotations

from pathlib import Path
from urllib.parse import quote, unquote
from uuid import uuid4

from apps.api.src.storage.object_storage import StoredObject


class LocalObjectStorage:
    def __init__(self, root: Path, url_prefix: str = "/uploads") -> None:
        self.root = root.resolve()
        self.url_prefix = "/" + url_prefix.strip("/")
        self.root.mkdir(parents=True, exist_ok=True)

    def put(self, key: str, data: bytes, content_type: str) -> StoredObject:
        del content_type
        destination = self._path_for_key(key)
        destination.parent.mkdir(parents=True, exist_ok=True)
        temporary = destination.with_name(f".{destination.name}.{uuid4().hex}.tmp")
        try:
            temporary.write_bytes(data)
            temporary.replace(destination)
        finally:
            temporary.unlink(missing_ok=True)
        return StoredObject(key=key, url=f"{self.url_prefix}/{quote(key, safe='/')}")

    def delete(self, key: str) -> None:
        self._path_for_key(key).unlink(missing_ok=True)

    def key_from_url(self, url: str) -> str | None:
        prefix = f"{self.url_prefix}/"
        if not url.startswith(prefix):
            return None
        key = unquote(url.removeprefix(prefix))
        self._require_safe_key(key)
        return key

    def _path_for_key(self, key: str) -> Path:
        return self._require_safe_key(key)

    def _require_safe_key(self, key: str) -> Path:
        if not key or key.startswith(("/", "\\")):
            raise ValueError("Object key must be a non-empty relative path.")
        destination = (self.root / key).resolve()
        if not destination.is_relative_to(self.root):
            raise ValueError("Object key escapes the configured storage root.")
        return destination

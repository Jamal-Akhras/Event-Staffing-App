from __future__ import annotations

from typing import Any
from urllib.parse import quote, unquote, urlsplit

from apps.api.src.storage.object_storage import StoredObject


class S3ObjectStorage:
    def __init__(self, client: Any, bucket: str, public_base_url: str) -> None:
        self.client = client
        self.bucket = bucket
        self.public_base_url = public_base_url.rstrip("/")
        parsed = urlsplit(self.public_base_url)
        self._public_origin = f"{parsed.scheme}://{parsed.netloc}"
        self._public_path = parsed.path.rstrip("/")

    def put(self, key: str, data: bytes, content_type: str) -> StoredObject:
        self.client.put_object(
            Bucket=self.bucket,
            Key=key,
            Body=data,
            ContentType=content_type,
            CacheControl="public, max-age=31536000, immutable",
        )
        url = f"{self.public_base_url}/{quote(key, safe='/')}"
        return StoredObject(key=key, url=url)

    def delete(self, key: str) -> None:
        self.client.delete_object(Bucket=self.bucket, Key=key)

    def key_from_url(self, url: str) -> str | None:
        parsed = urlsplit(url)
        if f"{parsed.scheme}://{parsed.netloc}" != self._public_origin:
            return None
        prefix = f"{self._public_path}/"
        if not parsed.path.startswith(prefix):
            return None
        key = unquote(parsed.path.removeprefix(prefix))
        if (
            not key
            or key.startswith(("/", "\\"))
            or "\\" in key
            or any(part in {".", ".."} for part in key.split("/"))
        ):
            return None
        return key

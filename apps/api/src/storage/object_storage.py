from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class StoredObject:
    key: str
    url: str


class ObjectStorage(Protocol):
    def put(self, key: str, data: bytes, content_type: str) -> StoredObject: ...

    def delete(self, key: str) -> None: ...

    def key_from_url(self, url: str) -> str | None: ...

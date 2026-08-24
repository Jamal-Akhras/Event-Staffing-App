from __future__ import annotations

import re
from hashlib import sha256
from uuid import uuid4

from starlette.concurrency import run_in_threadpool

from apps.api.src.storage.object_storage import ObjectStorage, StoredObject
from apps.api.src.unit_of_work import RequestUnitOfWork

_SAFE_SEGMENT = re.compile(r"^[A-Za-z0-9_-]{1,128}$")


def avatar_key(owner_kind: str, owner_id: str, extension: str) -> str:
    return f"{avatar_prefix(owner_kind, owner_id)}{uuid4().hex}{extension}"


def avatar_prefix(owner_kind: str, owner_id: str) -> str:
    return f"{owner_kind}/{_safe_segment(owner_id)}/avatars/"


def venue_photo_key(venue_id: str, extension: str) -> str:
    return f"{venue_photo_prefix(venue_id)}{uuid4().hex}{extension}"


def venue_photo_prefix(venue_id: str) -> str:
    return f"venues/{_safe_segment(venue_id)}/photos/"


async def store_image(
    storage: ObjectStorage,
    unit_of_work: RequestUnitOfWork,
    key: str,
    data: bytes,
    content_type: str,
    previous_url: str | None = None,
    previous_key_prefix: str | None = None,
) -> StoredObject:
    stored = await run_in_threadpool(storage.put, key, data, content_type)
    unit_of_work.after_rollback(lambda: storage.delete(stored.key))
    previous_key = storage.key_from_url(previous_url) if previous_url else None
    if (
        previous_key
        and previous_key_prefix
        and previous_key.startswith(previous_key_prefix)
        and previous_key != stored.key
    ):
        unit_of_work.after_commit(lambda: storage.delete(previous_key))
    return stored


def retire_objects_after_commit(
    storage: ObjectStorage,
    unit_of_work: RequestUnitOfWork,
    urls: set[str],
    key_prefix: str,
) -> None:
    keys = {
        key
        for url in urls
        if (key := storage.key_from_url(url)) and key.startswith(key_prefix)
    }
    for key in keys:
        unit_of_work.after_commit(lambda object_key=key: storage.delete(object_key))


def _safe_segment(value: str) -> str:
    if _SAFE_SEGMENT.fullmatch(value):
        return value
    return sha256(value.encode("utf-8")).hexdigest()

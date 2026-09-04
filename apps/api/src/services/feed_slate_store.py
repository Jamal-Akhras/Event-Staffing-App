from __future__ import annotations

import json
import time
from dataclasses import dataclass
from typing import Protocol

from apps.api.src.config import get_redis_url, use_in_memory_backends

_PREFIX = "feedslate:"
SLATE_TTL_SECONDS = 600


@dataclass(frozen=True)
class SlateEntry:
    shift_id: str
    reasons: list[str]


class FeedSlateStore(Protocol):
    def save(self, worker_id: str, slate_id: str, entries: list[SlateEntry]) -> None:
        ...

    def get(self, worker_id: str, slate_id: str) -> list[SlateEntry] | None:
        ...


def _key(worker_id: str, slate_id: str) -> str:
    return f"{_PREFIX}{worker_id}:{slate_id}"


def _encode(entries: list[SlateEntry]) -> str:
    return json.dumps([{"s": e.shift_id, "r": e.reasons} for e in entries], separators=(",", ":"))


def _decode(raw: str) -> list[SlateEntry]:
    return [SlateEntry(shift_id=row["s"], reasons=row["r"]) for row in json.loads(raw)]


class InMemoryFeedSlateStore:
    def __init__(self) -> None:
        self._slates: dict[str, tuple[float, str]] = {}

    def save(self, worker_id: str, slate_id: str, entries: list[SlateEntry]) -> None:
        self._slates[_key(worker_id, slate_id)] = (
            time.time() + SLATE_TTL_SECONDS,
            _encode(entries),
        )

    def get(self, worker_id: str, slate_id: str) -> list[SlateEntry] | None:
        stored = self._slates.get(_key(worker_id, slate_id))
        if stored is None:
            return None
        expires_at, raw = stored
        if expires_at <= time.time():
            del self._slates[_key(worker_id, slate_id)]
            return None
        return _decode(raw)

    def clear(self) -> None:
        self._slates.clear()


class RedisFeedSlateStore:
    def __init__(self, redis_url: str) -> None:
        import redis

        self._client = redis.Redis.from_url(redis_url, decode_responses=True)

    def save(self, worker_id: str, slate_id: str, entries: list[SlateEntry]) -> None:
        self._client.set(_key(worker_id, slate_id), _encode(entries), ex=SLATE_TTL_SECONDS)

    def get(self, worker_id: str, slate_id: str) -> list[SlateEntry] | None:
        raw = self._client.get(_key(worker_id, slate_id))
        return _decode(raw) if raw is not None else None


def _build() -> FeedSlateStore:
    if use_in_memory_backends():
        return InMemoryFeedSlateStore()
    return RedisFeedSlateStore(get_redis_url())


_store: FeedSlateStore = _build()


def get_feed_slate_store() -> FeedSlateStore:
    return _store

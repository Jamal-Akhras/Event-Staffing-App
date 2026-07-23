"""Token revocation denylist for JWT access tokens.

A revoked token's ``jti`` is stored until its original expiry. ``decode_access_token``
consults the denylist and rejects any token whose ``jti`` is present, so logout and
leaked-token revocation take effect immediately rather than waiting out the 24h expiry.

Two implementations, selected the same way as the Redis-backed rate limiter:
- ``RedisTokenDenylist`` for shared, multi-replica, restart-surviving revocation.
- ``InMemoryTokenDenylist`` for development and tests (per-process, lost on restart).
"""

from __future__ import annotations

import time
from typing import Protocol

from apps.api.src.config import get_redis_url, use_in_memory_backends

_DENYLIST_KEY_PREFIX = "jwt:denylist:"


class TokenDenylist(Protocol):
    def revoke(self, jti: str, ttl_seconds: int) -> None:
        """Mark ``jti`` as revoked for ``ttl_seconds``. Non-positive TTLs are ignored."""
        raise NotImplementedError

    def is_revoked(self, jti: str) -> bool:
        raise NotImplementedError


class InMemoryTokenDenylist:
    def __init__(self) -> None:
        self._revoked_until: dict[str, float] = {}

    def revoke(self, jti: str, ttl_seconds: int) -> None:
        if ttl_seconds <= 0:
            return
        self._revoked_until[jti] = time.time() + ttl_seconds

    def is_revoked(self, jti: str) -> bool:
        expires_at = self._revoked_until.get(jti)
        if expires_at is None:
            return False
        if expires_at <= time.time():
            del self._revoked_until[jti]
            return False
        return True

    def clear(self) -> None:
        self._revoked_until.clear()


class RedisTokenDenylist:
    def __init__(self, redis_url: str) -> None:
        import redis

        self._client = redis.Redis.from_url(redis_url, decode_responses=True)

    def revoke(self, jti: str, ttl_seconds: int) -> None:
        if ttl_seconds <= 0:
            return
        self._client.set(_DENYLIST_KEY_PREFIX + jti, "1", ex=ttl_seconds)

    def is_revoked(self, jti: str) -> bool:
        return self._client.exists(_DENYLIST_KEY_PREFIX + jti) == 1


def _build_denylist() -> TokenDenylist:
    if use_in_memory_backends():
        return InMemoryTokenDenylist()
    return RedisTokenDenylist(get_redis_url())


_denylist: TokenDenylist = _build_denylist()


def get_token_denylist() -> TokenDenylist:
    return _denylist

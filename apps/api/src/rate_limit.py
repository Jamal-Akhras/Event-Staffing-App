from __future__ import annotations

import logging

from slowapi import Limiter
from slowapi.util import get_remote_address
from starlette.requests import Request

from apps.api.src.config import get_redis_url, trust_forwarded_for, use_in_memory_backends

log = logging.getLogger(__name__)


def client_ip(request: Request) -> str:
    if trust_forwarded_for():
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            client = forwarded_for.split(",")[0].strip()
            if client:
                return client
    return get_remote_address(request)


def actor_or_ip(request: Request) -> str:
    authorization = request.headers.get("Authorization", "")
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() == "bearer" and token:
        try:
            from apps.api.src.auth.jwt import decode_access_token

            user_id = decode_access_token(token).get("user_id")
            if user_id:
                return f"actor:{user_id}"
        except Exception:
            pass
    return f"ip:{client_ip(request)}"


def _build_limiter() -> Limiter:
    if use_in_memory_backends():
        log.warning(
            "Rate limiter is using in-memory storage. Limits are per-process and "
            "reset on restart. This is acceptable only in development."
        )
        return Limiter(key_func=client_ip)

    redis_url = get_redis_url()
    return Limiter(key_func=client_ip, storage_uri=redis_url)


limiter = _build_limiter()

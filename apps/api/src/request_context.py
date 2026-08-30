from __future__ import annotations

import re
from contextvars import ContextVar, Token
from dataclasses import dataclass

_SAFE_TOKEN = re.compile(r"^[A-Za-z0-9._:-]{1,64}$")
_CLIENT_SOURCES = {"web", "mobile", "worker", "system"}


@dataclass(frozen=True)
class RequestMetadata:
    request_id: str | None = None
    ip: str | None = None
    user_agent: str | None = None
    session_id: str | None = None
    app_version: str | None = None
    source: str = "api"


_CURRENT: ContextVar[RequestMetadata] = ContextVar("request_metadata", default=RequestMetadata())


def current_request_metadata() -> RequestMetadata:
    return _CURRENT.get()


def set_request_metadata(metadata: RequestMetadata) -> Token[RequestMetadata]:
    return _CURRENT.set(metadata)


def reset_request_metadata(token: Token[RequestMetadata]) -> None:
    _CURRENT.reset(token)


def metadata_from_headers(headers, request_id: str | None, client_ip: str | None) -> RequestMetadata:
    client = (headers.get("X-Client") or "").strip().lower()
    session_id = (headers.get("X-Session-Id") or "").strip()
    app_version = (headers.get("X-App-Version") or "").strip()
    user_agent = headers.get("User-Agent") or None
    return RequestMetadata(
        request_id=request_id,
        ip=client_ip,
        user_agent=user_agent[:400] if user_agent else None,
        session_id=session_id if _SAFE_TOKEN.fullmatch(session_id) else None,
        app_version=app_version[:40] if app_version else None,
        source=client if client in _CLIENT_SOURCES else "api",
    )

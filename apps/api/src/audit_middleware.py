from __future__ import annotations

import time

from starlette.concurrency import run_in_threadpool
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from apps.api.src.config import trust_forwarded_for
from apps.api.src.request_context import (
    RequestMetadata,
    metadata_from_headers,
    reset_request_metadata,
    set_request_metadata,
)

AUDITED_METHODS = {"POST", "PUT", "PATCH", "DELETE"}
SKIPPED_PATHS = {"/events"}


class AuditMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        metadata = metadata_from_headers(
            request.headers,
            getattr(request.state, "request_id", None),
            _client_ip(request),
        )
        token = set_request_metadata(metadata)
        started = time.perf_counter()
        status_code = 500
        try:
            response = await call_next(request)
            status_code = response.status_code
            return response
        finally:
            reset_request_metadata(token)
            if _should_audit(request):
                duration_ms = int((time.perf_counter() - started) * 1000)
                await run_in_threadpool(_record, request, status_code, duration_ms, metadata)


def _should_audit(request: Request) -> bool:
    return request.method in AUDITED_METHODS and request.url.path not in SKIPPED_PATHS


def _client_ip(request: Request) -> str | None:
    if trust_forwarded_for():
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()[:45]
    return request.client.host if request.client else None


def _record(request: Request, status_code: int, duration_ms: int, metadata: RequestMetadata) -> None:
    from apps.api.src.services.durable_events import record_durable

    route = request.scope.get("route")
    record_durable(
        "http.request",
        "audit",
        metadata=metadata,
        actor=getattr(request.state, "actor", None),
        subject_type="route",
        subject_id=getattr(route, "path", request.url.path),
        status_code=status_code,
        duration_ms=duration_ms,
        context={
            "method": request.method,
            "path": request.url.path,
            "query": dict(request.query_params),
        },
    )

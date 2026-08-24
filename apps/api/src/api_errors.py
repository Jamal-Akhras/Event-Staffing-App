from __future__ import annotations

from typing import Any

from fastapi import HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded

_STATUS_CODES = {
    400: "BAD_REQUEST",
    401: "AUTHENTICATION_REQUIRED",
    403: "ACCESS_FORBIDDEN",
    404: "NOT_FOUND",
    409: "CONFLICT",
    413: "PAYLOAD_TOO_LARGE",
    422: "VALIDATION_ERROR",
    429: "RATE_LIMITED",
}


def error_content(
    status_code: int,
    message: str,
    detail: Any | None = None,
    details: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    error: dict[str, Any] = {
        "code": _STATUS_CODES.get(status_code, "INTERNAL_ERROR"),
        "message": message,
    }
    if details:
        error["details"] = details
    return {"detail": message if detail is None else detail, "error": error}


async def http_exception_handler(_request: Request, exc: HTTPException) -> JSONResponse:
    message = exc.detail if isinstance(exc.detail, str) else "Request failed."
    return JSONResponse(
        status_code=exc.status_code,
        content=error_content(exc.status_code, message, detail=exc.detail),
        headers=exc.headers,
    )


async def validation_exception_handler(
    _request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    raw_errors = exc.errors()
    details = [
        {
            "field": ".".join(str(part) for part in item["loc"] if part != "body"),
            "message": item["msg"],
            "type": item["type"],
        }
        for item in raw_errors
    ]
    return JSONResponse(
        status_code=422,
        content=error_content(
            422,
            "Request validation failed.",
            detail=raw_errors,
            details=details,
        ),
    )


async def rate_limit_exception_handler(
    _request: Request,
    exc: RateLimitExceeded,
) -> JSONResponse:
    return JSONResponse(
        status_code=429,
        content=error_content(429, "Too many requests. Please try again later."),
        headers={"Retry-After": "60"},
    )

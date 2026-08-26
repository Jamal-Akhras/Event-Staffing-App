from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from apps.api.src.api_errors import (
    error_content,
    http_exception_handler,
    rate_limit_exception_handler,
    validation_exception_handler,
)
from apps.api.src.config import get_cors_origins, is_development
from apps.api.src.observability import init_sentry
from apps.api.src.rate_limit import limiter
from apps.api.src.request_middleware import RequestContextMiddleware
from apps.api.src.routes import auth, bookings, shifts, applications, workers, templates, messages, worker_feed
from apps.api.src.routes import uploads, accounts, notifications, ratings, auth_account, auth_password, markets, tenancy
from apps.api.src.routes import reports, auth_sso, billing
from apps.api.src.storage.config import get_storage_settings
from apps.api.src.services.health import readiness_snapshot
from apps.api.src.db.schema_guard import ensure_schema_current

log = logging.getLogger(__name__)

init_sentry()


@asynccontextmanager
async def lifespan(_app: FastAPI):
    ensure_schema_current()
    yield


documentation_paths = {} if is_development() else {
    "docs_url": None,
    "redoc_url": None,
    "openapi_url": None,
}
app = FastAPI(
    title="Event Staffing Platform API",
    version="0.1.0",
    lifespan=lifespan,
    **documentation_paths,
)
app.state.limiter = limiter
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(RateLimitExceeded, rate_limit_exception_handler)


@app.exception_handler(Exception)
async def unhandled_exception_handler(_request: Request, exc: Exception) -> JSONResponse:
    log.exception("unhandled exception: %s", exc)
    return JSONResponse(
        status_code=500,
        content=error_content(500, "Internal server error."),
    )


app.add_middleware(SlowAPIMiddleware)
app.add_middleware(RequestContextMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=get_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

storage_settings = get_storage_settings()
app.include_router(auth.router)
app.include_router(auth_account.router)
app.include_router(auth_password.router)
app.include_router(auth_sso.router)
app.include_router(accounts.router)
app.include_router(tenancy.router)
app.include_router(markets.router)
app.include_router(bookings.router)
app.include_router(shifts.router)
app.include_router(applications.router)
app.include_router(workers.router)
app.include_router(templates.router)
app.include_router(messages.router)
app.include_router(worker_feed.router)
app.include_router(uploads.router)
app.include_router(notifications.router)
app.include_router(ratings.router)
app.include_router(reports.router)
app.include_router(billing.router)

if storage_settings.backend == "local":
    storage_settings.local_directory.mkdir(parents=True, exist_ok=True)
    app.mount(
        "/uploads",
        StaticFiles(directory=str(storage_settings.local_directory)),
        name="uploads",
    )


@app.get("/live")
@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/ready")
def ready() -> JSONResponse:
    is_ready, components = readiness_snapshot()
    return JSONResponse(
        status_code=200 if is_ready else 503,
        content={"status": "ready" if is_ready else "unavailable", "components": components},
    )

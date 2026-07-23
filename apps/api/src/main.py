from __future__ import annotations

import logging
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi import _rate_limit_exceeded_handler

from apps.api.src.config import get_cors_origins
from apps.api.src.observability import init_sentry
from apps.api.src.rate_limit import limiter
from apps.api.src.routes import auth, bookings, shifts, applications, workers, templates, messages, worker_feed
from apps.api.src.routes import uploads, accounts, notifications, ratings, auth_account

log = logging.getLogger(__name__)

init_sentry()

_UPLOAD_DIR = Path(__file__).resolve().parent.parent / "uploads"
_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


app = FastAPI(title="Event Staffing Platform API", version="0.1.0")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


@app.exception_handler(Exception)
async def unhandled_exception_handler(_request: Request, exc: Exception) -> JSONResponse:
    """Catch otherwise-uncaught exceptions so the response goes through CORS middleware.

    Without this, Starlette's outer ServerErrorMiddleware returns a 500 that bypasses
    CORS — the browser then blocks the response as a CORS failure and the client sees
    a network error instead of the real 500.
    """
    log.exception("unhandled exception: %s", exc)
    return JSONResponse(status_code=500, content={"detail": "Internal server error."})


app.add_middleware(SlowAPIMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=get_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/uploads", StaticFiles(directory=str(_UPLOAD_DIR)), name="uploads")

app.include_router(auth.router)
app.include_router(auth_account.router)
app.include_router(accounts.router)
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


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[3]
ENV_PATH = PROJECT_ROOT / ".env"
DEFAULT_CORS_ORIGINS = "http://localhost:5173,http://127.0.0.1:5173"

load_dotenv(dotenv_path=ENV_PATH)


def get_env(name: str, default: str = "") -> str:
    return os.getenv(name, default)


def get_database_url() -> str:
    return normalize_database_url(get_env("DATABASE_URL", "sqlite+pysqlite:///./event_staffing.db"))


def normalize_database_url(database_url: str) -> str:
    if database_url.startswith("postgres://"):
        return "postgresql+psycopg://" + database_url.removeprefix("postgres://")
    if database_url.startswith("postgresql://"):
        return "postgresql+psycopg://" + database_url.removeprefix("postgresql://")
    return resolve_sqlite_file_url(database_url)


def resolve_sqlite_file_url(database_url: str) -> str:
    for prefix in ("sqlite+pysqlite:///", "sqlite:///"):
        if not database_url.startswith(prefix):
            continue
        path_value = database_url.removeprefix(prefix)
        if path_value == ":memory:" or Path(path_value).is_absolute():
            return database_url
        database_path = (PROJECT_ROOT / path_value).resolve()
        return f"{prefix}{database_path.as_posix()}"
    return database_url


def get_bool_env(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.lower() in {"1", "true", "yes", "on"}


def get_cors_origins() -> list[str]:
    value = get_env("CORS_ORIGINS", DEFAULT_CORS_ORIGINS)
    parsed = [origin.strip() for origin in value.split(",") if origin.strip()]
    if not parsed:
        return [origin.strip() for origin in DEFAULT_CORS_ORIGINS.split(",") if origin.strip()]
    return parsed


def get_environment() -> str:
    return get_env("ENVIRONMENT", "development").strip().lower()


def is_development() -> bool:
    return get_environment() == "development"


def use_in_memory_backends() -> bool:
    """Whether Redis-backed infrastructure (rate limit store, token denylist)
    should use the in-memory implementation instead of a real Redis server.

    True in development when REDIS_URL is unset, or when USE_IN_MEMORY is forced.
    Outside development this returns False — callers must fail loudly if REDIS_URL
    is missing rather than silently degrading to a non-shared in-memory store.
    """
    if get_bool_env("USE_IN_MEMORY", False):
        return True
    if is_development() and not get_env("REDIS_URL"):
        return True
    return False


def get_redis_url() -> str:
    """Return REDIS_URL, raising outside development if it is unset.

    In development an unset REDIS_URL is acceptable (callers fall back to
    in-memory). In any other environment a missing REDIS_URL is a fatal
    misconfiguration — we refuse to start rather than silently lose shared state.
    """
    redis_url = get_env("REDIS_URL")
    if redis_url:
        return redis_url
    if get_bool_env("USE_IN_MEMORY", False):
        return ""
    if is_development():
        return ""
    raise RuntimeError(
        "REDIS_URL must be set when ENVIRONMENT is not development. "
        "A shared Redis store is required for rate limiting and token revocation; "
        "the in-memory fallback is development-only."
    )


def trust_forwarded_for() -> bool:
    """Whether to trust the X-Forwarded-For header for the real client IP.

    Only enable this when the API runs behind a proxy/load balancer that
    overwrites or appends a trustworthy client IP. When false, the socket
    peer IP is used. Misconfiguring this is a spoofing risk, so it defaults off.
    """
    return get_bool_env("TRUST_FORWARDED_FOR", False)


def ensure_safe_startup_config(jwt_secret: str, default_secret: str) -> None:
    if get_environment() == "development":
        return
    if get_bool_env("DEV_MODE", False):
        raise RuntimeError("DEV_MODE must be false when ENVIRONMENT is not development.")
    if jwt_secret == default_secret or len(jwt_secret) < 32:
        raise RuntimeError(
            "JWT_SECRET_KEY must be non-default and at least 32 characters outside development."
        )

from __future__ import annotations

import os
from decimal import Decimal
from pathlib import Path
from urllib.parse import urlparse

from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[3]
ENV_PATH = PROJECT_ROOT / ".env"
DEFAULT_CORS_ORIGINS = "http://localhost:5173,http://127.0.0.1:5173"

load_dotenv(dotenv_path=ENV_PATH)


def get_env(name: str, default: str = "") -> str:
    return os.getenv(name, default)


def get_bool_env(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.lower() in {"1", "true", "yes", "on"}


def get_environment() -> str:
    return get_env("ENVIRONMENT", "development").strip().lower()


def is_development() -> bool:
    return get_environment() == "development"


def _forced_in_memory() -> bool:
    forced = get_bool_env("USE_IN_MEMORY", False)
    if forced and not is_development():
        raise RuntimeError("USE_IN_MEMORY is development-only.")
    return forced


def get_database_url() -> str:
    configured_url = get_env("DATABASE_URL")
    if not configured_url:
        if not is_development() and not _forced_in_memory():
            raise RuntimeError("DATABASE_URL must be set when ENVIRONMENT is not development.")
        configured_url = "sqlite+pysqlite:///./event_staffing.db"
    normalized_url = normalize_database_url(configured_url)
    if not is_development() and normalized_url.startswith("sqlite"):
        raise RuntimeError("DATABASE_URL must use PostgreSQL when ENVIRONMENT is not development.")
    return normalized_url


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


def get_cors_origins() -> list[str]:
    development = is_development()
    value = get_env("CORS_ORIGINS")
    if not value and not development:
        raise RuntimeError("CORS_ORIGINS must contain the deployed web origin when ENVIRONMENT is not development.")
    parsed = [origin.strip() for origin in value.split(",") if origin.strip()]
    if not parsed:
        if not development:
            raise RuntimeError("CORS_ORIGINS must contain at least one origin when ENVIRONMENT is not development.")
        parsed = DEFAULT_CORS_ORIGINS.split(",")
    for origin in parsed:
        parsed_origin = urlparse(origin)
        if origin == "*" or parsed_origin.scheme not in {"http", "https"} or not parsed_origin.netloc:
            raise RuntimeError("CORS_ORIGINS entries must be absolute HTTP(S) origins and cannot be '*'.")
        if not development and parsed_origin.scheme != "https":
            raise RuntimeError("CORS_ORIGINS entries must use HTTPS outside development.")
    return parsed


def get_web_base_url() -> str:
    value = get_env("WEB_BASE_URL", "http://localhost:5173").rstrip("/")
    parsed = urlparse(value)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise RuntimeError("WEB_BASE_URL must be an absolute HTTP(S) URL.")
    if not is_development() and parsed.scheme != "https":
        raise RuntimeError("WEB_BASE_URL must use HTTPS outside development.")
    return value


def get_platform_fee_percent() -> Decimal:
    value = get_env("PLATFORM_FEE_PERCENT").strip()
    if not value:
        raise RuntimeError("PLATFORM_FEE_PERCENT must be set (percentage of wages charged on completed shifts).")
    percent = Decimal(value)
    if percent < 0 or percent > 100:
        raise RuntimeError("PLATFORM_FEE_PERCENT must be between 0 and 100.")
    return percent


def feed_ranking_enabled() -> bool:
    return get_bool_env("FEED_RANKING_ENABLED", False)


def use_in_memory_repositories() -> bool:
    if _forced_in_memory():
        return True
    if get_env("DATABASE_URL"):
        return False
    if is_development():
        return True
    raise RuntimeError("DATABASE_URL must be set when ENVIRONMENT is not development.")


def use_in_memory_backends() -> bool:
    return _forced_in_memory() or (is_development() and not get_env("REDIS_URL"))


def get_redis_url() -> str:
    redis_url = get_env("REDIS_URL")
    if redis_url or _forced_in_memory() or is_development():
        return redis_url
    raise RuntimeError(
        "REDIS_URL must be set when ENVIRONMENT is not development. "
        "A shared Redis store is required for rate limiting and token revocation; "
        "the in-memory fallback is development-only."
    )


def trust_forwarded_for() -> bool:
    return get_bool_env("TRUST_FORWARDED_FOR", False)


def ensure_safe_startup_config(jwt_secret: str, default_secret: str) -> None:
    if is_development():
        return
    if get_bool_env("DEV_MODE", False):
        raise RuntimeError("DEV_MODE must be false when ENVIRONMENT is not development.")
    _forced_in_memory()
    if jwt_secret == default_secret or len(jwt_secret) < 32:
        raise RuntimeError("JWT_SECRET_KEY must be non-default and at least 32 characters outside development.")

import pytest

from apps.api.src.config import (
    PROJECT_ROOT,
    get_cors_origins,
    get_database_url,
    normalize_database_url,
    resolve_sqlite_file_url,
    use_in_memory_repositories,
)


def test_resolve_sqlite_file_url_anchors_relative_paths_to_project_root():
    database_url = resolve_sqlite_file_url("sqlite+pysqlite:///./event_staffing.db")

    expected_path = (PROJECT_ROOT / "event_staffing.db").resolve().as_posix()
    assert database_url == f"sqlite+pysqlite:///{expected_path}"


def test_resolve_sqlite_file_url_leaves_external_urls_unchanged():
    database_url = "postgresql://user:password@localhost/event_staffing"

    assert resolve_sqlite_file_url(database_url) == database_url


def test_normalize_database_url_uses_psycopg_for_postgres_urls():
    database_url = "postgresql://user:password@localhost/event_staffing"

    assert normalize_database_url(database_url) == "postgresql+psycopg://user:password@localhost/event_staffing"


def test_normalize_database_url_accepts_postgres_scheme_alias():
    database_url = "postgres://user:password@localhost/event_staffing"

    assert normalize_database_url(database_url) == "postgresql+psycopg://user:password@localhost/event_staffing"


def test_get_cors_origins_parses_comma_separated_env(monkeypatch):
    monkeypatch.setenv(
        "CORS_ORIGINS",
        "https://app.example.com, http://localhost:5173,https://admin.example.com ",
    )

    assert get_cors_origins() == [
        "https://app.example.com",
        "http://localhost:5173",
        "https://admin.example.com",
    ]


def test_get_cors_origins_falls_back_to_default_when_blank(monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "development")
    monkeypatch.setenv("CORS_ORIGINS", "  ,  ")

    assert get_cors_origins() == [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]


def test_production_requires_database_url(monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.setenv("USE_IN_MEMORY", "false")
    monkeypatch.delenv("DATABASE_URL", raising=False)

    with pytest.raises(RuntimeError, match="DATABASE_URL"):
        get_database_url()
    with pytest.raises(RuntimeError, match="DATABASE_URL"):
        use_in_memory_repositories()


def test_production_rejects_sqlite_database(monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.setenv("DATABASE_URL", "sqlite+pysqlite:///./production.db")

    with pytest.raises(RuntimeError, match="PostgreSQL"):
        get_database_url()


def test_production_requires_cors_origins(monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.delenv("CORS_ORIGINS", raising=False)

    with pytest.raises(RuntimeError, match="CORS_ORIGINS"):
        get_cors_origins()


def test_production_rejects_insecure_cors_origin(monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.setenv("CORS_ORIGINS", "http://app.example.com")

    with pytest.raises(RuntimeError, match="HTTPS"):
        get_cors_origins()

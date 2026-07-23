from apps.api.src.config import PROJECT_ROOT, get_cors_origins, normalize_database_url, resolve_sqlite_file_url


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
    monkeypatch.setenv("CORS_ORIGINS", "  ,  ")

    assert get_cors_origins() == [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]

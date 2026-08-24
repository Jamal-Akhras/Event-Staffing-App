from __future__ import annotations

import os
from datetime import UTC, datetime
from decimal import Decimal

if os.environ.get("TEST_DATABASE_URL"):
    os.environ["DATABASE_URL"] = os.environ["TEST_DATABASE_URL"]
    os.environ.setdefault("USE_IN_MEMORY", "false")
os.environ.setdefault("USE_IN_MEMORY", "true")
os.environ.setdefault("DEV_MODE", "true")

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

from apps.api.src.config import get_bool_env, get_env


def _database_backend() -> str:
    if get_bool_env("USE_IN_MEMORY"):
        return "in-memory"
    database_url = get_env("DATABASE_URL")
    if not database_url:
        raise RuntimeError(
            "Tests with USE_IN_MEMORY=false require DATABASE_URL (or TEST_DATABASE_URL). "
            "Refusing to run against the silent in-memory fallback in deps.py."
        )
    if database_url.startswith(("postgres://", "postgresql")):
        return "postgres"
    return "sqlite"


DATABASE_BACKEND = _database_backend()


def _assert_disposable_database() -> None:
    from apps.api.src.db.database import engine

    name = engine.url.database or ""
    if "test" not in name.lower():
        raise RuntimeError(
            f"Refusing destructive test cleanup against database '{name}'. "
            "Point TEST_DATABASE_URL at a disposable database whose name contains "
            "'test' (for example event_staffing_test)."
        )


def _delete_all_rows() -> None:
    from apps.api.src.db import models  # noqa: F401  registers tables on Base.metadata
    from apps.api.src.db.database import Base, engine
    from apps.api.src.db.tenancy_models import MarketModel

    with engine.begin() as connection:
        for table in reversed(Base.metadata.sorted_tables):
            connection.execute(table.delete())
        connection.execute(
            MarketModel.__table__.insert().values(
                market_id="bath-gb",
                name="Bath",
                country="GB",
                currency="GBP",
                timezone="Europe/London",
                high_pay_threshold=Decimal("15.00"),
                is_active=True,
                created_at=datetime(2026, 1, 1, tzinfo=UTC),
            )
        )


if DATABASE_BACKEND != "in-memory":
    _assert_disposable_database()


def pytest_runtest_setup(item: pytest.Item) -> None:
    if item.get_closest_marker("postgres") is None:
        return
    if DATABASE_BACKEND == "postgres":
        return
    if get_bool_env("REQUIRE_POSTGRES_TESTS"):
        pytest.fail(
            f"REQUIRE_POSTGRES_TESTS is set but the test backend is '{DATABASE_BACKEND}'. "
            "PostgreSQL-marked tests must run, not skip, on the postgres CI leg."
        )
    pytest.skip("requires PostgreSQL (set TEST_DATABASE_URL to a postgres test database)")


@pytest.fixture(autouse=True)
def clean_database_tables():
    if DATABASE_BACKEND != "in-memory":
        _delete_all_rows()
    yield


@pytest.fixture(autouse=True)
def reset_rate_limiter():
    from apps.api.src.main import app

    app.state.limiter.reset()
    yield
    app.state.limiter.reset()


@pytest.fixture(autouse=True)
def restore_dependency_overrides():
    from apps.api.src.main import app

    saved = dict(app.dependency_overrides)
    yield
    app.dependency_overrides.clear()
    app.dependency_overrides.update(saved)


@pytest.fixture(autouse=True)
def reset_in_memory_idempotency():
    from apps.api.src.services.idempotency import clear_in_memory_idempotency

    clear_in_memory_idempotency()
    yield
    clear_in_memory_idempotency()


@pytest.fixture()
def repo_session():
    if DATABASE_BACKEND == "postgres":
        from apps.api.src.db.database import SessionLocal

        session = SessionLocal()
        yield session
        session.close()
        return

    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    event.listen(
        engine,
        "connect",
        lambda connection, _: connection.execute("PRAGMA foreign_keys=ON"),
    )
    from apps.api.src.db import models  # noqa: F401  registers tables on Base.metadata
    from apps.api.src.db.database import Base

    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)()
    yield session
    session.close()
    engine.dispose()

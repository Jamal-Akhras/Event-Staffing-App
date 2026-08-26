from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect, text


PROJECT_ROOT = Path(__file__).resolve().parents[3]


def test_sqlite_migrations_reach_head(tmp_path, monkeypatch):
    database_path = tmp_path / "migrations.db"
    database_url = f"sqlite+pysqlite:///{database_path.as_posix()}"
    monkeypatch.setenv("DATABASE_URL", database_url)
    config = Config(str(PROJECT_ROOT / "apps/api/alembic.ini"))

    command.upgrade(config, "head")

    engine = create_engine(database_url)
    inspector = inspect(engine)
    expected_tables = {
        "organisations",
        "venues",
        "markets",
        "organisation_memberships",
        "users",
        "shifts",
        "shift_templates",
        "outbox_events",
        "notification_deliveries",
        "user_notification_preferences",
        "push_tokens",
        "reports",
        "idempotency_records",
    }
    assert expected_tables.issubset(set(inspector.get_table_names()))

    expected_links = {
        "users": "active_venue_id",
        "shifts": "venue_id",
        "shift_templates": "venue_id",
    }
    for table, link_column in expected_links.items():
        columns = {column["name"] for column in inspector.get_columns(table)}
        assert link_column in columns
        foreign_keys = inspector.get_foreign_keys(table)
        assert any(
            key["referred_table"] == "venues"
            and key["constrained_columns"] == [link_column]
            for key in foreign_keys
        )

    for table in ("venues", "worker_profiles"):
        columns = {column["name"] for column in inspector.get_columns(table)}
        assert "market_id" in columns
        assert any(
            key["referred_table"] == "markets"
            and key["constrained_columns"] == ["market_id"]
            and key["options"]["ondelete"] == "RESTRICT"
            for key in inspector.get_foreign_keys(table)
        )

    rating_columns = {column["name"]: column for column in inspector.get_columns("ratings")}
    assert rating_columns["rater_id"]["nullable"] is False

    user_columns = {column["name"] for column in inspector.get_columns("users")}
    assert {"session_version", "deactivated_at", "anonymized_at"}.issubset(user_columns)

    shift_indexes = {index["name"] for index in inspector.get_indexes("shifts")}
    assert "ix_shifts_open_venue_start" in shift_indexes

    for table in ("shifts", "worker_profiles", "shift_templates"):
        pay_rate = next(column for column in inspector.get_columns(table) if column["name"] == "pay_rate")
        assert pay_rate["type"].precision == 12
        assert pay_rate["type"].scale == 2

    for table in ("bookings", "applications"):
        shift_key = next(
            key for key in inspector.get_foreign_keys(table)
            if key["constrained_columns"] == ["shift_id"]
        )
        assert shift_key["options"]["ondelete"] == "RESTRICT"

    notification_key = next(
        key for key in inspector.get_foreign_keys("notifications")
        if key["constrained_columns"] == ["shift_id"]
    )
    assert notification_key["options"]["ondelete"] == "SET NULL"

    with engine.connect() as connection:
        version = connection.execute(text("SELECT version_num FROM alembic_version")).scalar_one()
        assert version == "032"

    command.downgrade(config, "022")
    downgraded_rating_columns = {
        column["name"] for column in inspect(engine).get_columns("ratings")
    }
    assert "rater_id" not in downgraded_rating_columns


def test_organisation_migration_backfills_and_reverses(tmp_path, monkeypatch):
    database_path = tmp_path / "backfill.db"
    database_url = f"sqlite+pysqlite:///{database_path.as_posix()}"
    monkeypatch.setenv("DATABASE_URL", database_url)
    config = Config(str(PROJECT_ROOT / "apps/api/alembic.ini"))
    command.upgrade(config, "020")
    engine = create_engine(database_url)

    with engine.begin() as connection:
        connection.execute(
            text(
                "INSERT INTO accounts (account_id, name, country, currency, created_at) "
                "VALUES ('venue-1', 'The Test Tavern', 'GB', 'GBP', '2030-01-01 10:00:00')"
            )
        )
        connection.execute(
            text(
                "INSERT INTO users (user_id, email, hashed_password, role, account_id, is_active, "
                "created_at, updated_at, email_verified) VALUES "
                "('operator-1', 'operator@example.com', 'hash', 'operator', 'venue-1', 1, "
                "'2030-01-01 10:00:00', '2030-01-01 10:00:00', 1)"
            )
        )

    command.upgrade(config, "021")
    with engine.connect() as connection:
        assert connection.execute(text("SELECT name FROM organisations")).scalar_one() == "The Test Tavern"
        assert connection.execute(text("SELECT organisation_id FROM venues")).scalar_one() == "venue-1"
        assert connection.execute(text("SELECT role FROM organisation_memberships")).scalar_one() == "owner"
        assert connection.execute(text("SELECT active_venue_id FROM users")).scalar_one() == "venue-1"

    command.downgrade(config, "020")
    with engine.connect() as connection:
        assert connection.execute(text("SELECT name FROM accounts")).scalar_one() == "The Test Tavern"
        assert connection.execute(text("SELECT account_id FROM users")).scalar_one() == "venue-1"


def test_market_migration_backfills_bath_and_reverses(tmp_path, monkeypatch):
    database_path = tmp_path / "market-backfill.db"
    database_url = f"sqlite+pysqlite:///{database_path.as_posix()}"
    monkeypatch.setenv("DATABASE_URL", database_url)
    config = Config(str(PROJECT_ROOT / "apps/api/alembic.ini"))
    command.upgrade(config, "021")
    engine = create_engine(database_url)

    with engine.begin() as connection:
        connection.execute(
            text(
                "INSERT INTO organisations "
                "(organisation_id, name, country, currency, created_at) VALUES "
                "('org-1', 'Bath Group', 'GB', 'GBP', '2030-01-01 10:00:00')"
            )
        )
        connection.execute(
            text(
                "INSERT INTO venues "
                "(venue_id, organisation_id, name, country, currency, created_at, default_location) "
                "VALUES ('venue-1', 'org-1', 'Bath Tavern', 'GB', 'GBP', "
                "'2030-01-01 10:00:00', ' Bath ')"
            )
        )
        connection.execute(
            text(
                "INSERT INTO worker_profiles "
                "(worker_id, display_name, role, city, experience_years, reliability_score, "
                "badges, languages, updated_at) VALUES "
                "('worker-1', 'Alex', 'Bartender', 'BATH', 2, 1, '[]', '[]', "
                "'2030-01-01 10:00:00')"
            )
        )

    command.upgrade(config, "022")
    with engine.connect() as connection:
        market = connection.execute(
            text(
                "SELECT name, country, currency, timezone, high_pay_threshold "
                "FROM markets WHERE market_id = 'bath-gb'"
            )
        ).one()
        assert tuple(market) == ("Bath", "GB", "GBP", "Europe/London", 15)
        assert connection.execute(text("SELECT market_id FROM venues")).scalar_one() == "bath-gb"
        assert connection.execute(text("SELECT market_id FROM worker_profiles")).scalar_one() == "bath-gb"

    inspector = inspect(engine)
    assert "ix_shifts_open_venue_start" in {
        index["name"] for index in inspector.get_indexes("shifts")
    }

    command.downgrade(config, "021")
    downgraded = inspect(engine)
    assert "markets" not in downgraded.get_table_names()
    assert "market_id" not in {column["name"] for column in downgraded.get_columns("venues")}
    assert "market_id" not in {
        column["name"] for column in downgraded.get_columns("worker_profiles")
    }
    assert "ix_shifts_open_venue_start" not in {
        index["name"] for index in downgraded.get_indexes("shifts")
    }

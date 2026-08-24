from __future__ import annotations

import pytest
from sqlalchemy import inspect, text

from apps.api.src.db.database import engine

pytestmark = pytest.mark.postgres


def test_postgres_has_market_and_open_feed_indexes():
    inspector = inspect(engine)
    assert "ix_venues_market_id" in {index["name"] for index in inspector.get_indexes("venues")}
    assert "ix_worker_profiles_market_id" in {
        index["name"] for index in inspector.get_indexes("worker_profiles")
    }
    with engine.connect() as connection:
        index_definition = connection.execute(
            text(
                "SELECT indexdef FROM pg_indexes "
                "WHERE tablename = 'shifts' AND indexname = 'ix_shifts_open_venue_start'"
            )
        ).scalar_one()
    assert "(venue_id, start_time, shift_id)" in index_definition
    assert "WHERE" in index_definition and "status" in index_definition

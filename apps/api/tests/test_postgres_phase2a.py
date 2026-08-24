from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest
from sqlalchemy import delete, inspect, text
from sqlalchemy.exc import IntegrityError

from apps.api.src.db.database import engine
from apps.api.src.db.models import BookingModel, NotificationModel, ShiftModel
from apps.api.src.models.shift import Shift
from apps.api.src.repositories.sqlalchemy_shift_repository import SqlAlchemyShiftRepository
from packages.domain.src.booking_state import BookingState

pytestmark = pytest.mark.postgres

TIMESTAMP_COLUMNS = {
    "markets": {"created_at"},
    "organisations": {"created_at"},
    "venues": {"created_at"},
    "organisation_memberships": {"created_at"},
    "bookings": {
        "start_time",
        "end_time",
        "created_at",
        "confirmed_at",
        "checked_in_at",
        "checked_out_at",
        "approved_at",
        "paid_at",
        "cancelled_at",
        "no_show_at",
    },
    "shifts": {"start_time", "end_time", "created_at"},
    "applications": {"start_time", "end_time", "created_at", "decided_at"},
    "worker_profiles": {"updated_at"},
    "users": {"created_at", "updated_at", "password_changed_at"},
    "shift_templates": {"created_at", "updated_at"},
    "recurring_schedules": {"start_date", "end_date", "created_at", "last_generated_at"},
    "messages": {"read_at", "created_at"},
    "application_message_history": {"edited_at"},
    "notifications": {"created_at"},
    "ratings": {"created_at"},
    "worker_feed_states": {"created_at", "updated_at"},
}


def _shift(shift_id: str = "phase2a-shift") -> ShiftModel:
    now = datetime(2030, 1, 1, 9, 0, tzinfo=UTC)
    return ShiftModel(
        shift_id=shift_id,
        operator_id="phase2a-operator",
        role="Bartender",
        location="Bath",
        start_time=now + timedelta(hours=1),
        end_time=now + timedelta(hours=5),
        pay_rate=Decimal("15.37"),
        status="open",
        created_at=now,
        workers_needed=1,
        workers_filled=0,
        currency="GBP",
    )


def test_postgres_schema_uses_timestamptz_and_exact_numeric():
    inspector = inspect(engine)
    for table, expected_columns in TIMESTAMP_COLUMNS.items():
        columns = {column["name"]: column for column in inspector.get_columns(table)}
        for column_name in expected_columns:
            assert columns[column_name]["type"].timezone is True

    for table in ("shifts", "worker_profiles", "shift_templates", "markets"):
        column_name = "high_pay_threshold" if table == "markets" else "pay_rate"
        pay_rate = next(column for column in inspector.get_columns(table) if column["name"] == column_name)
        assert pay_rate["type"].precision == 12
        assert pay_rate["type"].scale == 2


def test_postgres_round_trips_decimal_money_and_utc(repo_session):
    now = datetime(2030, 6, 1, 11, 0, tzinfo=UTC)
    repository = SqlAlchemyShiftRepository(repo_session)
    repository.save(
        Shift(
            shift_id="phase2a-decimal",
            operator_id="phase2a-operator",
            role="Bartender",
            location="Bath",
            start_time=now,
            end_time=now + timedelta(hours=4),
            pay_rate=Decimal("15.37"),
            notes=None,
            status="open",
            created_at=now,
            workers_needed=1,
        )
    )
    repo_session.commit()
    repo_session.expire_all()

    stored = repository.get("phase2a-decimal")

    assert stored is not None
    assert stored.pay_rate == Decimal("15.37")
    assert isinstance(stored.pay_rate, Decimal)
    assert stored.start_time.utcoffset() == timedelta(0)


def test_postgres_prevents_deleting_shift_with_booking(repo_session):
    shift = _shift("phase2a-protected")
    repo_session.add(shift)
    repo_session.flush()
    repo_session.add(
        BookingModel(
            booking_id="phase2a-booking",
            shift_id=shift.shift_id,
            worker_id="phase2a-worker",
            operator_id=shift.operator_id,
            start_time=shift.start_time,
            end_time=shift.end_time,
            state=BookingState.CONFIRMED,
            created_at=shift.created_at,
        )
    )
    repo_session.commit()

    with pytest.raises(IntegrityError):
        repo_session.execute(delete(ShiftModel).where(ShiftModel.shift_id == shift.shift_id))
        repo_session.flush()
    repo_session.rollback()

    assert repo_session.get(ShiftModel, shift.shift_id) is not None
    assert repo_session.get(BookingModel, "phase2a-booking") is not None


def test_postgres_shift_delete_retains_notification(repo_session):
    shift = _shift("phase2a-notification-shift")
    notification = NotificationModel(
        notification_id="phase2a-notification",
        worker_id="phase2a-worker",
        type="invited",
        title="Shift invitation",
        body="A venue invited you",
        shift_id=shift.shift_id,
        read=False,
        created_at=shift.created_at,
    )
    repo_session.add(shift)
    repo_session.flush()
    repo_session.add(notification)
    repo_session.commit()

    repo_session.execute(delete(ShiftModel).where(ShiftModel.shift_id == shift.shift_id))
    repo_session.commit()
    repo_session.expire_all()

    retained = repo_session.get(NotificationModel, notification.notification_id)
    assert retained is not None
    assert retained.shift_id is None


def test_postgres_foreign_keys_encode_deletion_policy():
    with engine.connect() as connection:
        rows = connection.execute(
            text(
                "SELECT tc.table_name, kcu.column_name, rc.delete_rule "
                "FROM information_schema.table_constraints tc "
                "JOIN information_schema.key_column_usage kcu "
                "ON tc.constraint_name = kcu.constraint_name "
                "AND tc.constraint_schema = kcu.constraint_schema "
                "JOIN information_schema.referential_constraints rc "
                "ON tc.constraint_name = rc.constraint_name "
                "AND tc.constraint_schema = rc.constraint_schema "
                "WHERE tc.constraint_type = 'FOREIGN KEY' "
                "AND tc.table_name IN ('bookings', 'applications', 'notifications') "
                "AND kcu.column_name = 'shift_id'"
            )
        ).all()

    policies = {(row.table_name, row.column_name): row.delete_rule for row in rows}
    assert policies[("bookings", "shift_id")] == "RESTRICT"
    assert policies[("applications", "shift_id")] == "RESTRICT"
    assert policies[("notifications", "shift_id")] == "SET NULL"

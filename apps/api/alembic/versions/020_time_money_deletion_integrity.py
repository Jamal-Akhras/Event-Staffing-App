from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "020"
down_revision = "019"
branch_labels = None
depends_on = None

TIMESTAMP_COLUMNS = {
    "accounts": ("created_at",),
    "bookings": (
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
    ),
    "shifts": ("start_time", "end_time", "created_at"),
    "applications": ("start_time", "end_time", "created_at", "decided_at"),
    "worker_profiles": ("updated_at",),
    "users": ("created_at", "updated_at", "password_changed_at"),
    "shift_templates": ("created_at", "updated_at"),
    "recurring_schedules": ("start_date", "end_date", "created_at", "last_generated_at"),
    "messages": ("read_at", "created_at"),
    "application_message_history": ("edited_at",),
    "notifications": ("created_at",),
    "ratings": ("created_at",),
    "worker_feed_states": ("created_at", "updated_at"),
}

MONEY_COLUMNS = {
    "shifts": "pay_rate",
    "worker_profiles": "pay_rate",
    "shift_templates": "pay_rate",
}


def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        _upgrade_postgresql_types()
        _replace_shift_foreign_keys()
    else:
        _upgrade_sqlite_types_and_foreign_keys()
    _add_notification_shift_foreign_key()


def downgrade() -> None:
    bind = op.get_bind()
    _drop_notification_shift_foreign_key()
    if bind.dialect.name == "postgresql":
        _restore_shift_foreign_keys()
        _downgrade_postgresql_types()
    else:
        _downgrade_sqlite_types_and_foreign_keys()


def _upgrade_postgresql_types() -> None:
    for table, columns in TIMESTAMP_COLUMNS.items():
        for column in columns:
            op.alter_column(
                table,
                column,
                type_=sa.DateTime(timezone=True),
                postgresql_using=f'{column} AT TIME ZONE \'UTC\'',
            )
    for table, column in MONEY_COLUMNS.items():
        op.alter_column(
            table,
            column,
            type_=sa.Numeric(12, 2),
            postgresql_using=f"round({column}::numeric, 2)",
        )


def _downgrade_postgresql_types() -> None:
    for table, column in MONEY_COLUMNS.items():
        op.alter_column(
            table,
            column,
            type_=sa.Float(),
            postgresql_using=f"{column}::double precision",
        )
    for table, columns in TIMESTAMP_COLUMNS.items():
        for column in columns:
            op.alter_column(
                table,
                column,
                type_=sa.DateTime(timezone=False),
                postgresql_using=f'{column} AT TIME ZONE \'UTC\'',
            )


def _replace_shift_foreign_keys() -> None:
    _set_shift_foreign_keys("RESTRICT")


def _restore_shift_foreign_keys() -> None:
    _set_shift_foreign_keys("CASCADE")


def _set_shift_foreign_keys(ondelete: str) -> None:
    constraints = (
        ("bookings", "fk_bookings_shift_id_shifts"),
        ("applications", "fk_applications_shift_id_shifts"),
    )
    for table, constraint in constraints:
        op.drop_constraint(constraint, table, type_="foreignkey")
        op.create_foreign_key(
            constraint,
            table,
            "shifts",
            ["shift_id"],
            ["shift_id"],
            ondelete=ondelete,
        )


def _upgrade_sqlite_types_and_foreign_keys() -> None:
    with op.batch_alter_table("shifts") as batch:
        batch.alter_column("pay_rate", existing_type=sa.Float(), type_=sa.Numeric(12, 2))
    with op.batch_alter_table("worker_profiles") as batch:
        batch.alter_column("pay_rate", existing_type=sa.Float(), type_=sa.Numeric(12, 2))
    with op.batch_alter_table("shift_templates") as batch:
        batch.alter_column("pay_rate", existing_type=sa.Float(), type_=sa.Numeric(12, 2))
    _batch_set_shift_foreign_keys("RESTRICT")


def _downgrade_sqlite_types_and_foreign_keys() -> None:
    _batch_set_shift_foreign_keys("CASCADE")
    with op.batch_alter_table("shift_templates") as batch:
        batch.alter_column("pay_rate", existing_type=sa.Numeric(12, 2), type_=sa.Float())
    with op.batch_alter_table("worker_profiles") as batch:
        batch.alter_column("pay_rate", existing_type=sa.Numeric(12, 2), type_=sa.Float())
    with op.batch_alter_table("shifts") as batch:
        batch.alter_column("pay_rate", existing_type=sa.Numeric(12, 2), type_=sa.Float())


def _batch_set_shift_foreign_keys(ondelete: str) -> None:
    constraints = (
        ("bookings", "fk_bookings_shift_id_shifts"),
        ("applications", "fk_applications_shift_id_shifts"),
    )
    for table, constraint in constraints:
        with op.batch_alter_table(table) as batch:
            batch.drop_constraint(constraint, type_="foreignkey")
            batch.create_foreign_key(
                constraint,
                "shifts",
                ["shift_id"],
                ["shift_id"],
                ondelete=ondelete,
            )


def _add_notification_shift_foreign_key() -> None:
    bind = op.get_bind()
    bind.execute(
        sa.text(
            "UPDATE notifications SET shift_id = NULL "
            "WHERE shift_id IS NOT NULL AND NOT EXISTS "
            "(SELECT 1 FROM shifts WHERE shifts.shift_id = notifications.shift_id)"
        )
    )
    if bind.dialect.name == "sqlite":
        with op.batch_alter_table("notifications") as batch:
            batch.create_foreign_key(
                "fk_notifications_shift_id_shifts",
                "shifts",
                ["shift_id"],
                ["shift_id"],
                ondelete="SET NULL",
            )
        return
    op.create_foreign_key(
        "fk_notifications_shift_id_shifts",
        "notifications",
        "shifts",
        ["shift_id"],
        ["shift_id"],
        ondelete="SET NULL",
    )


def _drop_notification_shift_foreign_key() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "sqlite":
        with op.batch_alter_table("notifications") as batch:
            batch.drop_constraint("fk_notifications_shift_id_shifts", type_="foreignkey")
        return
    op.drop_constraint("fk_notifications_shift_id_shifts", "notifications", type_="foreignkey")

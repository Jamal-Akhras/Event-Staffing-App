from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "046"
down_revision = "045"
branch_labels = None
depends_on = None

_EXCEPTION_KINDS = "'available', 'unavailable'"
_TIME_OFF_STATUSES = "'pending', 'approved', 'declined', 'withdrawn'"
_MAX_INTERVAL_SECONDS = 366 * 24 * 60 * 60


def _duration_check(start_column: str, end_column: str) -> str:
    if op.get_bind().dialect.name == "sqlite":
        return (
            f"(julianday({end_column}) - julianday({start_column})) * 86400 "
            f"<= {_MAX_INTERVAL_SECONDS}"
        )
    return (
        f"EXTRACT(EPOCH FROM ({end_column} - {start_column})) "
        f"<= {_MAX_INTERVAL_SECONDS}"
    )


def upgrade() -> None:
    with op.batch_alter_table("worker_profiles") as batch:
        batch.add_column(
            sa.Column(
                "marketplace_enabled",
                sa.Boolean(),
                nullable=True,
                server_default=sa.true(),
            )
        )
    op.execute(
        sa.text("UPDATE worker_profiles SET marketplace_enabled = true WHERE marketplace_enabled IS NULL")
    )
    with op.batch_alter_table("worker_profiles") as batch:
        batch.alter_column(
            "marketplace_enabled",
            existing_type=sa.Boolean(),
            nullable=False,
            server_default=sa.true(),
        )

    op.create_table(
        "worker_availability_rules",
        sa.Column("rule_id", sa.String(), primary_key=True),
        sa.Column(
            "worker_id",
            sa.String(),
            sa.ForeignKey("worker_profiles.worker_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("timezone", sa.String(100), nullable=False),
        sa.Column("weekday", sa.Integer(), nullable=False),
        sa.Column("start_minute", sa.Integer(), nullable=False),
        sa.Column("duration_minutes", sa.Integer(), nullable=False),
        sa.Column("effective_from", sa.Date(), nullable=False),
        sa.Column("effective_until", sa.Date(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("weekday BETWEEN 0 AND 6", name="ck_availability_rules_weekday"),
        sa.CheckConstraint(
            "start_minute BETWEEN 0 AND 1439", name="ck_availability_rules_start_minute"
        ),
        sa.CheckConstraint(
            "duration_minutes BETWEEN 1 AND 1440", name="ck_availability_rules_duration"
        ),
        sa.CheckConstraint(
            "effective_until IS NULL OR effective_until >= effective_from",
            name="ck_availability_rules_effective_dates",
        ),
    )
    op.create_index(
        "ix_availability_rules_worker_effective",
        "worker_availability_rules",
        ["worker_id", "effective_from", "effective_until"],
    )

    op.create_table(
        "worker_availability_exceptions",
        sa.Column("exception_id", sa.String(), primary_key=True),
        sa.Column(
            "worker_id",
            sa.String(),
            sa.ForeignKey("worker_profiles.worker_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("kind", sa.String(16), nullable=False),
        sa.Column("start_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("end_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("note", sa.String(500), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            f"kind IN ({_EXCEPTION_KINDS})", name="ck_availability_exceptions_kind"
        ),
        sa.CheckConstraint(
            "end_time > start_time", name="ck_availability_exceptions_time_order"
        ),
        sa.CheckConstraint(
            _duration_check("start_time", "end_time"),
            name="ck_availability_exceptions_max_interval",
        ),
    )
    op.create_index(
        "ix_availability_exceptions_worker_interval",
        "worker_availability_exceptions",
        ["worker_id", "start_time", "end_time"],
    )

    op.create_table(
        "time_off_requests",
        sa.Column("request_id", sa.String(), primary_key=True),
        sa.Column(
            "worker_id",
            sa.String(),
            sa.ForeignKey("worker_profiles.worker_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "venue_id",
            sa.String(),
            sa.ForeignKey("venues.venue_id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("start_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("end_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("reason", sa.String(1000), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("decided_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("decided_by_user_id", sa.String(), nullable=True),
        sa.CheckConstraint(
            f"status IN ({_TIME_OFF_STATUSES})", name="ck_time_off_requests_status"
        ),
        sa.CheckConstraint("end_time > start_time", name="ck_time_off_requests_time_order"),
        sa.CheckConstraint(
            _duration_check("start_time", "end_time"),
            name="ck_time_off_requests_max_interval",
        ),
        sa.CheckConstraint(
            "((status IN ('approved', 'declined')) AND decided_at IS NOT NULL "
            "AND decided_by_user_id IS NOT NULL) OR "
            "((status IN ('pending', 'withdrawn')) AND decided_at IS NULL "
            "AND decided_by_user_id IS NULL)",
            name="ck_time_off_requests_decision_metadata",
        ),
    )
    op.create_index(
        "ix_time_off_requests_venue_status_start",
        "time_off_requests",
        ["venue_id", "status", "start_time"],
    )
    op.create_index(
        "ix_time_off_requests_worker_interval",
        "time_off_requests",
        ["worker_id", "start_time", "end_time"],
    )


def downgrade() -> None:
    op.drop_index("ix_time_off_requests_worker_interval", table_name="time_off_requests")
    op.drop_index("ix_time_off_requests_venue_status_start", table_name="time_off_requests")
    op.drop_table("time_off_requests")
    op.drop_index(
        "ix_availability_exceptions_worker_interval",
        table_name="worker_availability_exceptions",
    )
    op.drop_table("worker_availability_exceptions")
    op.drop_index(
        "ix_availability_rules_worker_effective", table_name="worker_availability_rules"
    )
    op.drop_table("worker_availability_rules")
    with op.batch_alter_table("worker_profiles") as batch:
        batch.drop_column("marketplace_enabled")

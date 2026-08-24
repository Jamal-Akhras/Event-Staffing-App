from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "022"
down_revision = "021"
branch_labels = None
depends_on = None

MARKET_LINKS = (
    ("venues", "fk_venues_market_id_markets"),
    ("worker_profiles", "fk_worker_profiles_market_id_markets"),
)


def upgrade() -> None:
    op.create_table(
        "markets",
        sa.Column("market_id", sa.String(), primary_key=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("country", sa.String(2), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False),
        sa.Column("timezone", sa.String(), nullable=False),
        sa.Column("high_pay_threshold", sa.Numeric(12, 2), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("high_pay_threshold >= 0", name="ck_markets_high_pay_nonnegative"),
    )
    op.get_bind().execute(
        sa.text(
            "INSERT INTO markets (market_id, name, country, currency, timezone, "
            "high_pay_threshold, is_active, created_at) VALUES "
            "('bath-gb', 'Bath', 'GB', 'GBP', 'Europe/London', 15.00, true, "
            "'2026-08-22 00:00:00+00')"
        )
    )
    for table, constraint in MARKET_LINKS:
        _add_market_link(table, constraint)
    _backfill_bath()
    predicate = sa.text("status = 'open'")
    op.create_index(
        "ix_shifts_open_venue_start",
        "shifts",
        ["venue_id", "start_time", "shift_id"],
        unique=False,
        postgresql_where=predicate,
        sqlite_where=predicate,
    )


def downgrade() -> None:
    op.drop_index("ix_shifts_open_venue_start", table_name="shifts")
    for table, constraint in reversed(MARKET_LINKS):
        _drop_market_link(table, constraint)
    op.drop_table("markets")


def _add_market_link(table: str, constraint: str) -> None:
    bind = op.get_bind()
    op.add_column(table, sa.Column("market_id", sa.String(), nullable=True))
    if bind.dialect.name == "sqlite":
        with op.batch_alter_table(table) as batch:
            batch.create_foreign_key(
                constraint,
                "markets",
                ["market_id"],
                ["market_id"],
                ondelete="RESTRICT",
            )
    else:
        op.create_foreign_key(
            constraint,
            table,
            "markets",
            ["market_id"],
            ["market_id"],
            ondelete="RESTRICT",
        )
    op.create_index(f"ix_{table}_market_id", table, ["market_id"])


def _drop_market_link(table: str, constraint: str) -> None:
    bind = op.get_bind()
    op.drop_index(f"ix_{table}_market_id", table_name=table)
    if bind.dialect.name == "sqlite":
        with op.batch_alter_table(table) as batch:
            batch.drop_constraint(constraint, type_="foreignkey")
            batch.drop_column("market_id")
        return
    op.drop_constraint(constraint, table, type_="foreignkey")
    op.drop_column(table, "market_id")


def _backfill_bath() -> None:
    bind = op.get_bind()
    bind.execute(
        sa.text(
            "UPDATE venues SET market_id = 'bath-gb' "
            "WHERE lower(trim(default_location)) = 'bath'"
        )
    )
    bind.execute(
        sa.text(
            "UPDATE worker_profiles SET market_id = 'bath-gb' "
            "WHERE lower(trim(city)) = 'bath'"
        )
    )

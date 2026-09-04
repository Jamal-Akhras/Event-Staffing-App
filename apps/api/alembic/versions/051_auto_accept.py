from __future__ import annotations

from alembic import op
import sqlalchemy as sa

from apps.api.src.db.types import UtcDateTime

revision = "051"
down_revision = "050"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "worker_auto_accept_rules",
        sa.Column("rule_id", sa.String(), primary_key=True),
        sa.Column("worker_id", sa.String(), nullable=False),
        sa.Column(
            "venue_id",
            sa.String(),
            sa.ForeignKey("venues.venue_id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("enabled", sa.Boolean(), nullable=False),
        sa.Column("roles", sa.JSON(), nullable=False),
        sa.Column("minimum_rate", sa.Numeric(12, 2), nullable=True),
        sa.Column("minimum_notice_hours", sa.Integer(), nullable=True),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("created_at", UtcDateTime(), nullable=False),
        sa.Column("updated_at", UtcDateTime(), nullable=False),
        sa.CheckConstraint(
            "minimum_rate IS NULL OR minimum_rate >= 0",
            name="ck_auto_accept_rules_minimum_rate",
        ),
        sa.CheckConstraint(
            "minimum_notice_hours IS NULL OR minimum_notice_hours >= 0",
            name="ck_auto_accept_rules_minimum_notice",
        ),
        sa.CheckConstraint("version >= 1", name="ck_auto_accept_rules_version"),
        sa.UniqueConstraint(
            "worker_id",
            "venue_id",
            name="uq_auto_accept_rules_worker_venue",
        ),
    )
    op.create_table(
        "auto_accept_attempts",
        sa.Column("attempt_id", sa.String(), primary_key=True),
        sa.Column(
            "offer_id",
            sa.String(),
            sa.ForeignKey("shift_offers.offer_id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("rule_id", sa.String(), nullable=True),
        sa.Column("rule_version", sa.Integer(), nullable=False),
        sa.Column("rule_snapshot", sa.JSON(), nullable=False),
        sa.Column("evaluated_at", UtcDateTime(), nullable=False),
        sa.Column("outcome", sa.String(length=12), nullable=False),
        sa.Column("reason", sa.String(length=500), nullable=True),
        sa.CheckConstraint(
            "outcome IN ('accepted', 'skipped', 'failed')",
            name="ck_auto_accept_attempts_outcome",
        ),
        sa.CheckConstraint(
            "rule_version >= 0",
            name="ck_auto_accept_attempts_rule_version",
        ),
        sa.UniqueConstraint(
            "offer_id",
            "rule_version",
            name="uq_auto_accept_attempts_offer_rule_version",
        ),
    )
    op.create_index(
        "ix_auto_accept_attempts_evaluated",
        "auto_accept_attempts",
        ["evaluated_at"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_auto_accept_attempts_evaluated",
        table_name="auto_accept_attempts",
    )
    op.drop_table("auto_accept_attempts")
    op.drop_table("worker_auto_accept_rules")

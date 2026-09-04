from __future__ import annotations

from alembic import op
import sqlalchemy as sa

from apps.api.src.db.types import UtcDateTime

revision = "057"
down_revision = "056"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "feed_ranking_appeals",
        sa.Column("appeal_id", sa.String(), primary_key=True),
        sa.Column("worker_id", sa.String(), nullable=False),
        sa.Column("shift_id", sa.String(), nullable=False),
        sa.Column("slate_id", sa.String(), nullable=True),
        sa.Column("reason", sa.String(length=1000), nullable=False),
        sa.Column("created_at", UtcDateTime(), nullable=False),
        sa.Column("reviewed_at", UtcDateTime(), nullable=True),
        sa.Column("reviewed_by_user_id", sa.String(), nullable=True),
        sa.Column("outcome_note", sa.String(length=1000), nullable=True),
        sa.CheckConstraint(
            "(reviewed_at IS NULL) = (reviewed_by_user_id IS NULL)",
            name="ck_feed_ranking_appeals_review",
        ),
    )
    op.create_index(
        "ix_feed_ranking_appeals_open",
        "feed_ranking_appeals",
        ["reviewed_at", "created_at"],
    )
    op.create_index(
        "ix_feed_ranking_appeals_worker",
        "feed_ranking_appeals",
        ["worker_id", "created_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_feed_ranking_appeals_worker", table_name="feed_ranking_appeals")
    op.drop_index("ix_feed_ranking_appeals_open", table_name="feed_ranking_appeals")
    op.drop_table("feed_ranking_appeals")

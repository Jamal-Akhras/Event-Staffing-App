from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "009_add_worker_feed_state"
down_revision = "008_add_integrity_constraints"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "worker_feed_states",
        sa.Column("worker_id", sa.String(), nullable=False),
        sa.Column("shift_id", sa.String(), nullable=False),
        sa.Column("action", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("worker_id", "shift_id", name="pk_worker_feed_states"),
        sa.ForeignKeyConstraint(["shift_id"], ["shifts.shift_id"], ondelete="CASCADE"),
        sa.CheckConstraint("action IN ('passed')", name="ck_worker_feed_states_action"),
    )
    op.create_index("ix_worker_feed_states_worker_id", "worker_feed_states", ["worker_id"])
    op.create_index("ix_worker_feed_states_shift_id", "worker_feed_states", ["shift_id"])


def downgrade() -> None:
    op.drop_index("ix_worker_feed_states_shift_id", table_name="worker_feed_states")
    op.drop_index("ix_worker_feed_states_worker_id", table_name="worker_feed_states")
    op.drop_table("worker_feed_states")

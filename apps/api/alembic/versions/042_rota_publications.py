from __future__ import annotations

import sqlalchemy as sa
from alembic import op

from apps.api.src.db.types import UtcDateTime

revision = "042"
down_revision = "041"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("shifts") as batch:
        batch.add_column(
            sa.Column("rota_state", sa.String(12), nullable=False, server_default="published")
        )
        batch.add_column(
            sa.Column("needs_attention", sa.Boolean(), nullable=False, server_default=sa.false())
        )
        batch.create_check_constraint("ck_shifts_rota_state", "rota_state IN ('draft', 'published')")
        batch.create_check_constraint(
            "ck_shifts_draft_is_assigned", "rota_state <> 'draft' OR origin = 'assigned'"
        )
        batch.create_check_constraint(
            "ck_shifts_draft_single_seat", "rota_state <> 'draft' OR workers_needed = 1"
        )

    op.create_table(
        "rota_publications",
        sa.Column("publication_id", sa.String(), primary_key=True),
        sa.Column(
            "venue_id",
            sa.String(),
            sa.ForeignKey("venues.venue_id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("week_start", sa.Date(), nullable=False),
        sa.Column("revision", sa.Integer(), nullable=False),
        sa.Column("published_at", UtcDateTime(), nullable=False),
        sa.Column("published_by_user_id", sa.String(), nullable=False),
        sa.Column("assignments", sa.JSON(), nullable=False),
        sa.UniqueConstraint(
            "venue_id", "week_start", "revision", name="uq_rota_publications_venue_week_revision"
        ),
        sa.CheckConstraint("revision >= 1", name="ck_rota_publications_revision"),
    )
    op.create_index("ix_rota_publications_venue_week", "rota_publications", ["venue_id", "week_start"])


def downgrade() -> None:
    op.drop_index("ix_rota_publications_venue_week", table_name="rota_publications")
    op.drop_table("rota_publications")
    with op.batch_alter_table("shifts") as batch:
        batch.drop_constraint("ck_shifts_draft_single_seat", type_="check")
        batch.drop_constraint("ck_shifts_draft_is_assigned", type_="check")
        batch.drop_constraint("ck_shifts_rota_state", type_="check")
        batch.drop_column("needs_attention")
        batch.drop_column("rota_state")

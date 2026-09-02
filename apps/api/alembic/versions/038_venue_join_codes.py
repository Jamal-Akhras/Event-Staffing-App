from __future__ import annotations

import sqlalchemy as sa
from alembic import op

from apps.api.src.db.types import UtcDateTime
from apps.api.src.models.worker_relationship import RELATIONSHIP_TYPES

revision = "038"
down_revision = "037"
branch_labels = None
depends_on = None

_TYPE_LIST = ", ".join(f"'{value}'" for value in RELATIONSHIP_TYPES)


def upgrade() -> None:
    op.create_table(
        "venue_join_codes",
        sa.Column("code", sa.String(length=40), primary_key=True),
        sa.Column(
            "venue_id",
            sa.String(),
            sa.ForeignKey("venues.venue_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("default_relationship_type", sa.String(length=20), nullable=False),
        sa.Column("default_role", sa.String(length=80), nullable=True),
        sa.Column("max_redemptions", sa.Integer(), nullable=False),
        sa.Column("expires_at", UtcDateTime(), nullable=True),
        sa.Column("revoked_at", UtcDateTime(), nullable=True),
        sa.Column("created_at", UtcDateTime(), nullable=False),
        sa.Column("created_by_user_id", sa.String(), nullable=False),
        sa.CheckConstraint(f"default_relationship_type IN ({_TYPE_LIST})", name="ck_venue_join_codes_type"),
        sa.CheckConstraint("max_redemptions >= 1", name="ck_venue_join_codes_max_redemptions"),
    )
    op.create_index("ix_venue_join_codes_venue", "venue_join_codes", ["venue_id"])

    op.create_table(
        "venue_join_code_redemptions",
        sa.Column("redemption_id", sa.String(), primary_key=True),
        sa.Column(
            "code",
            sa.String(length=40),
            sa.ForeignKey("venue_join_codes.code", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("venue_id", sa.String(), nullable=False),
        sa.Column("worker_id", sa.String(), nullable=False),
        sa.Column(
            "relationship_id",
            sa.String(),
            sa.ForeignKey("worker_relationships.relationship_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("redeemed_at", UtcDateTime(), nullable=False),
        sa.UniqueConstraint("code", "worker_id", name="uq_venue_join_code_redemptions_code_worker"),
    )
    op.create_index("ix_venue_join_code_redemptions_code", "venue_join_code_redemptions", ["code"])


def downgrade() -> None:
    op.drop_index("ix_venue_join_code_redemptions_code", table_name="venue_join_code_redemptions")
    op.drop_table("venue_join_code_redemptions")
    op.drop_index("ix_venue_join_codes_venue", table_name="venue_join_codes")
    op.drop_table("venue_join_codes")

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

from apps.api.src.db.types import UtcDateTime
from apps.api.src.models.worker_relationship import RELATIONSHIP_STATUSES, RELATIONSHIP_TYPES

revision = "037"
down_revision = "036"
branch_labels = None
depends_on = None

_TYPE_LIST = ", ".join(f"'{value}'" for value in RELATIONSHIP_TYPES)
_STATUS_LIST = ", ".join(f"'{value}'" for value in RELATIONSHIP_STATUSES)


def upgrade() -> None:
    op.create_table(
        "worker_relationships",
        sa.Column("relationship_id", sa.String(), primary_key=True),
        sa.Column(
            "venue_id",
            sa.String(),
            sa.ForeignKey("venues.venue_id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("worker_id", sa.String(), nullable=False),
        sa.Column("relationship_type", sa.String(length=20), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("default_role", sa.String(length=80), nullable=True),
        sa.Column("start_date", UtcDateTime(), nullable=True),
        sa.Column("end_date", UtcDateTime(), nullable=True),
        sa.Column("contracted_hours_per_week", sa.Numeric(5, 2), nullable=True),
        sa.Column("agreed_rate", sa.Numeric(12, 2), nullable=True),
        sa.Column("created_at", UtcDateTime(), nullable=False),
        sa.Column("updated_at", UtcDateTime(), nullable=False),
        sa.Column("created_by_user_id", sa.String(), nullable=True),
        sa.UniqueConstraint("venue_id", "worker_id", name="uq_worker_relationships_venue_worker"),
        sa.CheckConstraint(f"relationship_type IN ({_TYPE_LIST})", name="ck_worker_relationships_type"),
        sa.CheckConstraint(f"status IN ({_STATUS_LIST})", name="ck_worker_relationships_status"),
        sa.CheckConstraint(
            "contracted_hours_per_week IS NULL OR contracted_hours_per_week >= 0",
            name="ck_worker_relationships_contracted_hours",
        ),
        sa.CheckConstraint("agreed_rate IS NULL OR agreed_rate >= 0", name="ck_worker_relationships_agreed_rate"),
        sa.CheckConstraint(
            "end_date IS NULL OR end_date >= start_date",
            name="ck_worker_relationships_date_order",
        ),
    )
    op.create_index(
        "ix_worker_relationships_venue_status",
        "worker_relationships",
        ["venue_id", "status"],
    )
    op.create_index("ix_worker_relationships_worker", "worker_relationships", ["worker_id"])

    op.create_table(
        "relationship_transitions",
        sa.Column("transition_id", sa.String(), primary_key=True),
        sa.Column(
            "relationship_id",
            sa.String(),
            sa.ForeignKey("worker_relationships.relationship_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("from_relationship_type", sa.String(length=20), nullable=True),
        sa.Column("to_relationship_type", sa.String(length=20), nullable=False),
        sa.Column("from_status", sa.String(length=20), nullable=True),
        sa.Column("to_status", sa.String(length=20), nullable=False),
        sa.Column("occurred_at", UtcDateTime(), nullable=False),
        sa.Column("actor_user_id", sa.String(), nullable=True),
        sa.Column("reason", sa.String(length=500), nullable=True),
        sa.CheckConstraint(
            f"to_relationship_type IN ({_TYPE_LIST})",
            name="ck_relationship_transitions_to_type",
        ),
        sa.CheckConstraint(f"to_status IN ({_STATUS_LIST})", name="ck_relationship_transitions_to_status"),
    )
    op.create_index(
        "ix_relationship_transitions_relationship",
        "relationship_transitions",
        ["relationship_id", "occurred_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_relationship_transitions_relationship", table_name="relationship_transitions")
    op.drop_table("relationship_transitions")
    op.drop_index("ix_worker_relationships_worker", table_name="worker_relationships")
    op.drop_index("ix_worker_relationships_venue_status", table_name="worker_relationships")
    op.drop_table("worker_relationships")

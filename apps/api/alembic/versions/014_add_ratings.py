from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision = "014"
down_revision = "013"
branch_labels = None
depends_on = None


def _has_table(conn, table: str) -> bool:
    return table in inspect(conn).get_table_names()


def upgrade() -> None:
    bind = op.get_bind()
    if _has_table(bind, "ratings"):
        return
    op.create_table(
        "ratings",
        sa.Column("rating_id", sa.String(), primary_key=True),
        sa.Column(
            "booking_id",
            sa.String(),
            sa.ForeignKey("bookings.booking_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("rated_by_role", sa.String(), nullable=False),
        sa.Column("stars", sa.Integer(), nullable=False),
        sa.Column("comment", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("booking_id", "rated_by_role", name="uq_ratings_booking_role"),
        sa.CheckConstraint("stars >= 1 AND stars <= 5", name="ck_ratings_stars_range"),
    )
    op.create_index("ix_ratings_booking_id", "ratings", ["booking_id"])


def downgrade() -> None:
    bind = op.get_bind()
    if _has_table(bind, "ratings"):
        op.drop_index("ix_ratings_booking_id", table_name="ratings")
        op.drop_table("ratings")

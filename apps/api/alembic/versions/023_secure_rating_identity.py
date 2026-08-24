from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "023"
down_revision = "022"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    op.add_column("ratings", sa.Column("rater_id", sa.String(), nullable=True))
    bind.execute(
        sa.text(
            "UPDATE ratings SET rater_id = CASE "
            "WHEN rated_by_role = 'worker' THEN "
            "(SELECT worker_id FROM bookings WHERE bookings.booking_id = ratings.booking_id) "
            "ELSE (SELECT operator_id FROM bookings WHERE bookings.booking_id = ratings.booking_id) END"
        )
    )
    if bind.dialect.name == "sqlite":
        with op.batch_alter_table("ratings") as batch:
            batch.alter_column("rater_id", existing_type=sa.String(), nullable=False)
            batch.create_check_constraint(
                "ck_ratings_rated_by_role",
                "rated_by_role IN ('worker', 'operator')",
            )
        return
    op.alter_column("ratings", "rater_id", existing_type=sa.String(), nullable=False)
    op.create_check_constraint(
        "ck_ratings_rated_by_role",
        "ratings",
        "rated_by_role IN ('worker', 'operator')",
    )


def downgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "sqlite":
        with op.batch_alter_table("ratings") as batch:
            batch.drop_constraint("ck_ratings_rated_by_role", type_="check")
            batch.drop_column("rater_id")
        return
    op.drop_constraint("ck_ratings_rated_by_role", "ratings", type_="check")
    op.drop_column("ratings", "rater_id")

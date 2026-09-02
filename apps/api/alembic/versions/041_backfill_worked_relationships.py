from __future__ import annotations

from uuid import uuid4

import sqlalchemy as sa
from alembic import op

revision = "041"
down_revision = "040"
branch_labels = None
depends_on = None

_WORKED = sa.text(
    """
    SELECT c.account_id, c.worker_id, MIN(c.completed_at) AS first_worked, MAX(c.completed_at) AS last_worked
    FROM booking_charges c
    JOIN venues v ON v.venue_id = c.account_id
    WHERE NOT EXISTS (
        SELECT 1 FROM worker_relationships r
        WHERE r.venue_id = c.account_id AND r.worker_id = c.worker_id
    )
    GROUP BY c.account_id, c.worker_id
    """
)

_INSERT_RELATIONSHIP = sa.text(
    """
    INSERT INTO worker_relationships (
        relationship_id, venue_id, worker_id, relationship_type, status,
        start_date, created_at, updated_at
    ) VALUES (
        :relationship_id, :venue_id, :worker_id, 'one_off', 'active',
        :first_worked, :first_worked, :last_worked
    )
    """
)

_INSERT_TRANSITION = sa.text(
    """
    INSERT INTO relationship_transitions (
        transition_id, relationship_id, to_relationship_type, to_status, occurred_at, reason
    ) VALUES (
        :transition_id, :relationship_id, 'one_off', 'active', :first_worked,
        'Backfilled from completed shifts.'
    )
    """
)


def upgrade() -> None:
    connection = op.get_bind()
    for row in connection.execute(_WORKED).mappings().all():
        relationship_id = str(uuid4())
        connection.execute(
            _INSERT_RELATIONSHIP,
            {
                "relationship_id": relationship_id,
                "venue_id": row["account_id"],
                "worker_id": row["worker_id"],
                "first_worked": row["first_worked"],
                "last_worked": row["last_worked"],
            },
        )
        connection.execute(
            _INSERT_TRANSITION,
            {
                "transition_id": str(uuid4()),
                "relationship_id": relationship_id,
                "first_worked": row["first_worked"],
            },
        )


def downgrade() -> None:
    connection = op.get_bind()
    connection.execute(
        sa.text(
            """
            DELETE FROM relationship_transitions
            WHERE reason = 'Backfilled from completed shifts.'
            """
        )
    )
    connection.execute(
        sa.text(
            """
            DELETE FROM worker_relationships
            WHERE relationship_type = 'one_off'
              AND created_by_user_id IS NULL
              AND NOT EXISTS (
                  SELECT 1 FROM relationship_transitions t
                  WHERE t.relationship_id = worker_relationships.relationship_id
              )
            """
        )
    )

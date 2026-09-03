from __future__ import annotations

import json

from alembic import op
import sqlalchemy as sa

from apps.api.src.db.types import UtcDateTime

revision = "047"
down_revision = "046"
branch_labels = None
depends_on = None

_NEW_ORIGINS = "'assigned', 'team', 'pool', 'market'"
_OLD_ORIGINS = "'assigned', 'pool', 'market'"
_DEFAULT_NAMED = 24
_DEFAULT_POOL = 24
_DEFAULT_MARKET = 48


def _swap_origin_check(origins: str) -> None:
    with op.batch_alter_table("shifts") as batch:
        batch.drop_constraint("ck_shifts_origin", type_="check")
        batch.create_check_constraint("ck_shifts_origin", f"origin IN ({origins})")


def upgrade() -> None:
    _swap_origin_check(_NEW_ORIGINS)
    with op.batch_alter_table("shifts") as batch:
        batch.add_column(sa.Column("offer_team_at", UtcDateTime(), nullable=True))

    bind = op.get_bind()
    rows = bind.execute(
        sa.text("SELECT venue_id, escalation_policy FROM venues WHERE escalation_policy IS NOT NULL")
    ).fetchall()
    for venue_id, stored in rows:
        policy = stored if isinstance(stored, dict) else json.loads(stored)
        pool_hours = policy.get("pool_hours", _DEFAULT_POOL)
        upgraded = {
            "named_offer_hours": pool_hours if pool_hours is not None else _DEFAULT_NAMED,
            "team_hours": None,
            "pool_hours": pool_hours,
            "market_lead_hours": policy.get("market_lead_hours", _DEFAULT_MARKET),
        }
        bind.execute(
            sa.text("UPDATE venues SET escalation_policy = :policy WHERE venue_id = :venue_id"),
            {"policy": json.dumps(upgraded), "venue_id": venue_id},
        )


def downgrade() -> None:
    bind = op.get_bind()
    rows = bind.execute(
        sa.text("SELECT venue_id, escalation_policy FROM venues WHERE escalation_policy IS NOT NULL")
    ).fetchall()
    for venue_id, stored in rows:
        policy = stored if isinstance(stored, dict) else json.loads(stored)
        downgraded = {
            "pool_hours": policy.get("pool_hours"),
            "market_lead_hours": policy.get("market_lead_hours"),
        }
        bind.execute(
            sa.text("UPDATE venues SET escalation_policy = :policy WHERE venue_id = :venue_id"),
            {"policy": json.dumps(downgraded), "venue_id": venue_id},
        )

    with op.batch_alter_table("shifts") as batch:
        batch.drop_column("offer_team_at")
    _swap_origin_check(_OLD_ORIGINS)

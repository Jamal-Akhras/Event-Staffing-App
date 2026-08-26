from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "031"
down_revision = "030"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "partner_codes",
        sa.Column("code", sa.String(length=32), primary_key=True),
        sa.Column("label", sa.String(length=160), nullable=False),
        sa.Column("waiver_months", sa.Integer(), nullable=False),
        sa.Column("shift_cap", sa.Integer(), nullable=False),
        sa.Column("max_redemptions", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_by", sa.String(length=120), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("waiver_months > 0", name="ck_partner_codes_waiver_months_positive"),
        sa.CheckConstraint("shift_cap > 0", name="ck_partner_codes_shift_cap_positive"),
        sa.CheckConstraint("max_redemptions > 0", name="ck_partner_codes_max_redemptions_positive"),
    )
    op.create_table(
        "partner_code_redemptions",
        sa.Column("redemption_id", sa.String(), primary_key=True),
        sa.Column("code", sa.String(length=32), nullable=False),
        sa.Column("account_id", sa.String(), nullable=False),
        sa.Column("redeemed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("redeemed_by_user_id", sa.String(), nullable=False),
        sa.Column("fee_waived_until", sa.DateTime(timezone=True), nullable=False),
        sa.Column("shift_cap", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["code"], ["partner_codes.code"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["account_id"], ["venues.venue_id"], ondelete="CASCADE"),
        sa.UniqueConstraint("account_id", name="uq_partner_code_redemptions_account"),
        sa.CheckConstraint("shift_cap > 0", name="ck_partner_code_redemptions_shift_cap_positive"),
    )
    op.create_index("ix_partner_code_redemptions_code", "partner_code_redemptions", ["code"])


def downgrade() -> None:
    op.drop_index("ix_partner_code_redemptions_code", table_name="partner_code_redemptions")
    op.drop_table("partner_code_redemptions")
    op.drop_table("partner_codes")

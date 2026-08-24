from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "021"
down_revision = "020"
branch_labels = None
depends_on = None

LINKS = (
    ("users", "account_id", "active_venue_id", "SET NULL", "SET NULL"),
    ("shifts", "account_id", "venue_id", "RESTRICT", "SET NULL"),
    ("shift_templates", "account_id", "venue_id", "RESTRICT", "SET NULL"),
)


def upgrade() -> None:
    _create_organisation_tables()
    _copy_accounts_to_venues()
    for table, old_column, new_column, new_ondelete, _ in LINKS:
        _replace_link(table, old_column, new_column, "accounts", "venues", new_ondelete)
    _create_memberships()
    op.drop_table("accounts")


def downgrade() -> None:
    _create_accounts_table()
    _copy_venues_to_accounts()
    op.drop_table("organisation_memberships")
    for table, old_column, new_column, _, old_ondelete in reversed(LINKS):
        _replace_link(table, new_column, old_column, "venues", "accounts", old_ondelete)
    op.drop_table("venues")
    op.drop_table("organisations")


def _create_organisation_tables() -> None:
    op.create_table(
        "organisations",
        sa.Column("organisation_id", sa.String(), primary_key=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("country", sa.String(2), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "venues",
        sa.Column("venue_id", sa.String(), primary_key=True),
        sa.Column(
            "organisation_id",
            sa.String(),
            sa.ForeignKey("organisations.organisation_id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("country", sa.String(2), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        *_venue_detail_columns(),
    )
    op.create_index("ix_venues_organisation_id", "venues", ["organisation_id"])


def _copy_accounts_to_venues() -> None:
    bind = op.get_bind()
    bind.execute(
        sa.text(
            "INSERT INTO organisations (organisation_id, name, country, currency, created_at) "
            "SELECT account_id, name, country, currency, created_at FROM accounts"
        )
    )
    bind.execute(
        sa.text(
            "INSERT INTO venues (venue_id, organisation_id, name, country, currency, created_at, "
            "venue_type, contact_email, contact_phone, default_location, avatar_url, photos, "
            "notification_preferences) SELECT account_id, account_id, name, country, currency, "
            "created_at, venue_type, contact_email, contact_phone, default_location, avatar_url, "
            "photos, notification_preferences FROM accounts"
        )
    )


def _create_memberships() -> None:
    op.create_table(
        "organisation_memberships",
        sa.Column(
            "organisation_id",
            sa.String(),
            sa.ForeignKey("organisations.organisation_id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column(
            "user_id",
            sa.String(),
            sa.ForeignKey("users.user_id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("role", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("role IN ('owner', 'admin', 'manager')", name="ck_memberships_role"),
    )
    op.create_index("ix_organisation_memberships_user_id", "organisation_memberships", ["user_id"])
    op.get_bind().execute(
        sa.text(
            "INSERT INTO organisation_memberships (organisation_id, user_id, role, created_at) "
            "SELECT active_venue_id, user_id, 'owner', created_at FROM users "
            "WHERE role = 'operator' AND active_venue_id IS NOT NULL"
        )
    )


def _create_accounts_table() -> None:
    op.create_table(
        "accounts",
        sa.Column("account_id", sa.String(), primary_key=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("country", sa.String(2), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        *_venue_detail_columns(),
    )


def _copy_venues_to_accounts() -> None:
    op.get_bind().execute(
        sa.text(
            "INSERT INTO accounts (account_id, name, country, currency, created_at, venue_type, "
            "contact_email, contact_phone, default_location, avatar_url, photos, notification_preferences) "
            "SELECT venue_id, name, country, currency, created_at, venue_type, contact_email, "
            "contact_phone, default_location, avatar_url, photos, notification_preferences FROM venues"
        )
    )


def _venue_detail_columns() -> list[sa.Column]:
    return [
        sa.Column("venue_type", sa.String(), nullable=True),
        sa.Column("contact_email", sa.String(), nullable=True),
        sa.Column("contact_phone", sa.String(), nullable=True),
        sa.Column("default_location", sa.String(), nullable=True),
        sa.Column("avatar_url", sa.String(), nullable=True),
        sa.Column("photos", sa.JSON(), nullable=True),
        sa.Column("notification_preferences", sa.JSON(), nullable=True),
    ]


def _replace_link(
    table: str,
    old_column: str,
    new_column: str,
    old_target: str,
    new_target: str,
    ondelete: str,
) -> None:
    old_index = f"ix_{table}_{old_column}"
    new_index = f"ix_{table}_{new_column}"
    old_constraint = (
        f"{table}_account_id_fkey" if old_column == "account_id" else f"fk_{table}_{old_column}_{old_target}"
    )
    new_constraint = (
        f"{table}_account_id_fkey"
        if new_column == "account_id"
        else f"fk_{table}_{new_column}_{new_target}"
    )
    bind = op.get_bind()
    if bind.dialect.name == "sqlite":
        op.drop_index(old_index, table_name=table)
        with op.batch_alter_table(table) as batch:
            batch.drop_constraint(old_constraint, type_="foreignkey")
            batch.alter_column(old_column, new_column_name=new_column, existing_type=sa.String())
        with op.batch_alter_table(table) as batch:
            batch.create_foreign_key(
                new_constraint,
                new_target,
                [new_column],
                ["venue_id" if new_target == "venues" else "account_id"],
                ondelete=ondelete,
            )
        op.create_index(new_index, table, [new_column])
        return
    op.drop_index(old_index, table_name=table)
    op.drop_constraint(old_constraint, table, type_="foreignkey")
    op.alter_column(table, old_column, new_column_name=new_column)
    op.create_foreign_key(
        new_constraint,
        table,
        new_target,
        [new_column],
        ["venue_id" if new_target == "venues" else "account_id"],
        ondelete=ondelete,
    )
    op.create_index(new_index, table, [new_column])

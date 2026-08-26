from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision = "010"
down_revision = "009_add_worker_feed_state"
branch_labels = None
depends_on = None


def _has_column(conn, table: str, column: str) -> bool:
    return column in [c["name"] for c in inspect(conn).get_columns(table)]


def _has_index(conn, table: str, index: str) -> bool:
    return index in [i["name"] for i in inspect(conn).get_indexes(table)]


def _add_account_link(bind, table: str, index: str) -> None:
    has_column = _has_column(bind, table, "account_id")
    has_index = _has_index(bind, table, index)
    constraint = f"{table}_account_id_fkey"

    if bind.dialect.name == "sqlite":
        with op.batch_alter_table(table) as batch_op:
            if not has_column:
                batch_op.add_column(sa.Column("account_id", sa.String(), nullable=True))
                batch_op.create_foreign_key(
                    constraint,
                    "accounts",
                    ["account_id"],
                    ["account_id"],
                    ondelete="SET NULL",
                )
            if not has_index:
                batch_op.create_index(index, ["account_id"])
        return

    if not has_column:
        op.add_column(table, sa.Column("account_id", sa.String(), nullable=True))
        op.create_foreign_key(
            constraint,
            table,
            "accounts",
            ["account_id"],
            ["account_id"],
            ondelete="SET NULL",
        )
    if not has_index:
        op.create_index(index, table, ["account_id"])


def _drop_account_link(bind, table: str, index: str) -> None:
    has_column = _has_column(bind, table, "account_id")
    has_index = _has_index(bind, table, index)
    if not has_column and not has_index:
        return

    if bind.dialect.name == "sqlite":
        with op.batch_alter_table(table) as batch_op:
            if has_index:
                batch_op.drop_index(index)
            if has_column:
                batch_op.drop_constraint(f"{table}_account_id_fkey", type_="foreignkey")
                batch_op.drop_column("account_id")
        return

    if has_index:
        op.drop_index(index, table_name=table)
    if has_column:
        op.drop_constraint(f"{table}_account_id_fkey", table, type_="foreignkey")
        op.drop_column(table, "account_id")


def upgrade() -> None:
    bind = op.get_bind()


    op.create_table(
        "accounts",
        sa.Column("account_id", sa.String(), primary_key=True, nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("country", sa.String(2), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        if_not_exists=True,
    )

    _add_account_link(bind, "users", "ix_users_account_id")
    _add_account_link(bind, "shifts", "ix_shifts_account_id")
    _add_account_link(bind, "shift_templates", "ix_shift_templates_account_id")


def downgrade() -> None:
    bind = op.get_bind()
    _drop_account_link(bind, "shift_templates", "ix_shift_templates_account_id")
    _drop_account_link(bind, "shifts", "ix_shifts_account_id")
    _drop_account_link(bind, "users", "ix_users_account_id")
    op.drop_table("accounts")

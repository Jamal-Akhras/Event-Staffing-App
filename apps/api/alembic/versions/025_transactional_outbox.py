from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "025"
down_revision = "024"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    op.add_column("notifications", sa.Column("venue_id", sa.String(), nullable=True))
    op.add_column("notifications", sa.Column("action_kind", sa.String(length=32), nullable=True))
    op.add_column("notifications", sa.Column("action_entity_id", sa.String(), nullable=True))
    op.add_column("notifications", sa.Column("delivery_id", sa.String(), nullable=True))
    if bind.dialect.name == "sqlite":
        with op.batch_alter_table("notifications") as batch:
            batch.alter_column("worker_id", existing_type=sa.String(), nullable=True)
            batch.create_foreign_key(
                "fk_notifications_venue_id_venues",
                "venues",
                ["venue_id"],
                ["venue_id"],
                ondelete="SET NULL",
            )
    else:
        op.alter_column("notifications", "worker_id", existing_type=sa.String(), nullable=True)
        op.create_foreign_key(
            "fk_notifications_venue_id_venues",
            "notifications",
            "venues",
            ["venue_id"],
            ["venue_id"],
            ondelete="SET NULL",
        )
    op.create_index("ix_notifications_venue_id", "notifications", ["venue_id"])
    op.create_index("uq_notifications_delivery_id", "notifications", ["delivery_id"], unique=True)
    op.create_index(
        "ix_notifications_worker_unread_created",
        "notifications",
        ["worker_id", "read", "created_at"],
    )
    op.create_index(
        "ix_notifications_venue_unread_created",
        "notifications",
        ["venue_id", "read", "created_at"],
    )

    op.create_table(
        "outbox_events",
        sa.Column("event_id", sa.String(), primary_key=True),
        sa.Column("event_type", sa.String(length=100), nullable=False),
        sa.Column("aggregate_type", sa.String(length=50), nullable=False),
        sa.Column("aggregate_id", sa.String(), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("idempotency_key", sa.String(length=255), nullable=False, unique=True),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("available_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("attempt_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("locked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("locked_by", sa.String(length=100), nullable=True),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_error", sa.String(length=1000), nullable=True),
        sa.Column("dead_lettered_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index(
        "ix_outbox_events_pending",
        "outbox_events",
        ["available_at", "occurred_at"],
        postgresql_where=sa.text("processed_at IS NULL AND dead_lettered_at IS NULL"),
        sqlite_where=sa.text("processed_at IS NULL AND dead_lettered_at IS NULL"),
    )

    op.create_table(
        "notification_deliveries",
        sa.Column("delivery_id", sa.String(), primary_key=True),
        sa.Column(
            "event_id",
            sa.String(),
            sa.ForeignKey("outbox_events.event_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("recipient_kind", sa.String(length=20), nullable=False),
        sa.Column("recipient_id", sa.String(), nullable=False),
        sa.Column("channel", sa.String(length=20), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("attempt_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("next_attempt_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("locked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("locked_by", sa.String(length=100), nullable=True),
        sa.Column("delivered_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_error", sa.String(length=1000), nullable=True),
        sa.Column("idempotency_key", sa.String(length=255), nullable=False, unique=True),
        sa.CheckConstraint(
            "recipient_kind IN ('worker', 'venue', 'email')",
            name="ck_notification_deliveries_recipient_kind",
        ),
        sa.CheckConstraint(
            "channel IN ('in_app', 'email', 'push')",
            name="ck_notification_deliveries_channel",
        ),
        sa.CheckConstraint(
            "status IN ('pending', 'delivered', 'dead_letter')",
            name="ck_notification_deliveries_status",
        ),
    )
    op.create_index(
        "ix_notification_deliveries_pending",
        "notification_deliveries",
        ["status", "next_attempt_at"],
        postgresql_where=sa.text("status = 'pending'"),
        sqlite_where=sa.text("status = 'pending'"),
    )

    op.create_table(
        "user_notification_preferences",
        sa.Column(
            "user_id",
            sa.String(),
            sa.ForeignKey("users.user_id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("channels", sa.JSON(), nullable=False),
        sa.Column("categories", sa.JSON(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "push_tokens",
        sa.Column("push_token_id", sa.String(), primary_key=True),
        sa.Column(
            "user_id",
            sa.String(),
            sa.ForeignKey("users.user_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("token", sa.String(length=512), nullable=False, unique=True),
        sa.Column("platform", sa.String(length=10), nullable=False),
        sa.Column("device_id", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("platform IN ('ios', 'android')", name="ck_push_tokens_platform"),
        sa.UniqueConstraint("user_id", "device_id", name="uq_push_tokens_user_device"),
    )
    op.create_index("ix_push_tokens_user_id", "push_tokens", ["user_id"])


def downgrade() -> None:
    bind = op.get_bind()
    op.drop_index("ix_push_tokens_user_id", table_name="push_tokens")
    op.drop_table("push_tokens")
    op.drop_table("user_notification_preferences")
    op.drop_index("ix_notification_deliveries_pending", table_name="notification_deliveries")
    op.drop_table("notification_deliveries")
    op.drop_index("ix_outbox_events_pending", table_name="outbox_events")
    op.drop_table("outbox_events")
    op.drop_index("uq_notifications_delivery_id", table_name="notifications")
    bind.execute(sa.text("DROP INDEX IF EXISTS ix_notifications_venue_unread_created"))
    bind.execute(sa.text("DROP INDEX IF EXISTS ix_notifications_worker_unread_created"))
    op.drop_index("ix_notifications_venue_id", table_name="notifications")
    if bind.dialect.name == "sqlite":
        bind.execute(sa.text("DELETE FROM notifications WHERE worker_id IS NULL"))
        with op.batch_alter_table("notifications") as batch:
            batch.drop_constraint("fk_notifications_venue_id_venues", type_="foreignkey")
            batch.alter_column("worker_id", existing_type=sa.String(), nullable=False)
            batch.drop_column("delivery_id")
            batch.drop_column("action_entity_id")
            batch.drop_column("action_kind")
            batch.drop_column("venue_id")
        return
    bind.execute(sa.text("DELETE FROM notifications WHERE worker_id IS NULL"))
    op.drop_constraint("fk_notifications_venue_id_venues", "notifications", type_="foreignkey")
    op.alter_column("notifications", "worker_id", existing_type=sa.String(), nullable=False)
    op.drop_column("notifications", "delivery_id")
    op.drop_column("notifications", "action_entity_id")
    op.drop_column("notifications", "action_kind")
    op.drop_column("notifications", "venue_id")

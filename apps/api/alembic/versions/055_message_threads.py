from __future__ import annotations

from collections import defaultdict
from uuid import NAMESPACE_URL, uuid5

from alembic import op
import sqlalchemy as sa

from apps.api.src.db.types import UtcDateTime

revision = "055"
down_revision = "054"
branch_labels = None
depends_on = None


THREAD_SHAPE = """
(kind = 'direct' AND shift_id IS NOT NULL AND worker_id IS NOT NULL
 AND relationship_id IS NULL AND (application_id IS NOT NULL OR booking_id IS NOT NULL))
OR (kind = 'shift_group' AND shift_id IS NOT NULL AND worker_id IS NULL
 AND application_id IS NULL AND booking_id IS NULL AND relationship_id IS NULL)
OR (kind = 'employment' AND shift_id IS NULL AND worker_id IS NOT NULL
 AND application_id IS NULL AND booking_id IS NULL AND relationship_id IS NOT NULL)
"""

PARTY_SHAPE = """
(party_kind = 'user' AND user_id IS NOT NULL AND worker_id IS NULL)
OR (party_kind = 'worker' AND worker_id IS NOT NULL AND user_id IS NULL)
"""


def upgrade() -> None:
    op.create_table(
        "message_threads",
        sa.Column("thread_id", sa.String(), primary_key=True),
        sa.Column("kind", sa.String(length=16), nullable=False),
        sa.Column(
            "venue_id",
            sa.String(),
            sa.ForeignKey("venues.venue_id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "shift_id",
            sa.String(),
            sa.ForeignKey("shifts.shift_id", ondelete="RESTRICT"),
            nullable=True,
        ),
        sa.Column(
            "application_id",
            sa.String(),
            sa.ForeignKey("applications.application_id", ondelete="RESTRICT"),
            nullable=True,
        ),
        sa.Column(
            "booking_id",
            sa.String(),
            sa.ForeignKey("bookings.booking_id", ondelete="RESTRICT"),
            nullable=True,
        ),
        sa.Column(
            "relationship_id",
            sa.String(),
            sa.ForeignKey("worker_relationships.relationship_id", ondelete="RESTRICT"),
            nullable=True,
        ),
        sa.Column("worker_id", sa.String(), nullable=True),
        sa.Column("role_snapshot", sa.String(), nullable=True),
        sa.Column("venue_name_snapshot", sa.String(), nullable=False),
        sa.Column("created_at", UtcDateTime(), nullable=False),
        sa.CheckConstraint(THREAD_SHAPE, name="ck_message_threads_shape"),
    )
    op.create_index("ix_message_threads_venue", "message_threads", ["venue_id", "created_at"])
    op.create_index("ix_message_threads_worker", "message_threads", ["worker_id", "created_at"])
    _partial_index(
        "uq_message_threads_shift_group",
        "message_threads",
        ["shift_id"],
        "kind = 'shift_group'",
    )
    _partial_index(
        "uq_message_threads_employment",
        "message_threads",
        ["relationship_id"],
        "kind = 'employment'",
    )
    _partial_index(
        "uq_message_threads_direct_worker",
        "message_threads",
        ["shift_id", "worker_id"],
        "kind = 'direct'",
    )

    op.create_table(
        "message_thread_participants",
        sa.Column("participant_id", sa.String(), primary_key=True),
        sa.Column(
            "thread_id",
            sa.String(),
            sa.ForeignKey("message_threads.thread_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("party_kind", sa.String(length=8), nullable=False),
        sa.Column("user_id", sa.String(), nullable=True),
        sa.Column("worker_id", sa.String(), nullable=True),
        sa.Column("joined_at", UtcDateTime(), nullable=False),
        sa.Column("left_at", UtcDateTime(), nullable=True),
        sa.CheckConstraint(PARTY_SHAPE, name="ck_message_thread_participants_party"),
        sa.CheckConstraint(
            "left_at IS NULL OR left_at >= joined_at",
            name="ck_message_thread_participants_interval",
        ),
    )
    op.create_index(
        "ix_message_thread_participants_thread",
        "message_thread_participants",
        ["thread_id", "party_kind", "joined_at"],
    )
    _partial_index(
        "uq_message_thread_participants_active_user",
        "message_thread_participants",
        ["thread_id", "user_id"],
        "left_at IS NULL AND party_kind = 'user'",
    )
    _partial_index(
        "uq_message_thread_participants_active_worker",
        "message_thread_participants",
        ["thread_id", "worker_id"],
        "left_at IS NULL AND party_kind = 'worker'",
    )

    with op.batch_alter_table("messages") as batch:
        batch.add_column(
            sa.Column(
                "thread_id",
                sa.String(),
                sa.ForeignKey(
                    "message_threads.thread_id",
                    ondelete="RESTRICT",
                    name="fk_messages_thread_id",
                ),
                nullable=True,
            )
        )

    _backfill_direct_threads()

    op.create_table(
        "message_read_receipts",
        sa.Column("receipt_id", sa.String(), primary_key=True),
        sa.Column(
            "message_id",
            sa.String(),
            sa.ForeignKey("messages.message_id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("party_kind", sa.String(length=8), nullable=False),
        sa.Column("user_id", sa.String(), nullable=True),
        sa.Column("worker_id", sa.String(), nullable=True),
        sa.Column("read_at", UtcDateTime(), nullable=False),
        sa.CheckConstraint(PARTY_SHAPE, name="ck_message_read_receipts_party"),
        sa.UniqueConstraint("message_id", "user_id", name="uq_message_read_receipts_user"),
        sa.UniqueConstraint("message_id", "worker_id", name="uq_message_read_receipts_worker"),
    )
    op.create_index(
        "ix_message_read_receipts_party",
        "message_read_receipts",
        ["party_kind", "user_id", "worker_id", "read_at"],
    )
    _backfill_read_receipts()

    op.drop_index("ix_messages_booking_id", table_name="messages")
    op.drop_index("ix_messages_application_id", table_name="messages")
    op.drop_index("ix_messages_shift_id", table_name="messages")
    with op.batch_alter_table("messages") as batch:
        batch.drop_constraint("ck_messages_context_present", type_="check")
        batch.alter_column("thread_id", existing_type=sa.String(), nullable=False)
        batch.drop_column("read_at")
        batch.drop_column("booking_id")
        batch.drop_column("application_id")
        batch.drop_column("shift_id")
    op.create_index("ix_messages_thread_created", "messages", ["thread_id", "created_at"])


def downgrade() -> None:
    op.drop_index("ix_messages_thread_created", table_name="messages")
    with op.batch_alter_table("messages") as batch:
        batch.add_column(
            sa.Column(
                "shift_id",
                sa.String(),
                sa.ForeignKey("shifts.shift_id", ondelete="CASCADE", name="fk_messages_shift_id"),
                nullable=True,
            )
        )
        batch.add_column(
            sa.Column(
                "application_id",
                sa.String(),
                sa.ForeignKey(
                    "applications.application_id",
                    ondelete="CASCADE",
                    name="fk_messages_application_id",
                ),
                nullable=True,
            )
        )
        batch.add_column(
            sa.Column(
                "booking_id",
                sa.String(),
                sa.ForeignKey(
                    "bookings.booking_id",
                    ondelete="CASCADE",
                    name="fk_messages_booking_id",
                ),
                nullable=True,
            )
        )
        batch.add_column(sa.Column("read_at", UtcDateTime(), nullable=True))

    bind = op.get_bind()
    rows = bind.execute(
        sa.text(
            "SELECT m.message_id, t.shift_id, t.application_id, t.booking_id, "
            "MIN(r.read_at) AS read_at "
            "FROM messages m JOIN message_threads t ON t.thread_id = m.thread_id "
            "LEFT JOIN message_read_receipts r ON r.message_id = m.message_id "
            "GROUP BY m.message_id, t.shift_id, t.application_id, t.booking_id"
        )
    ).mappings()
    for row in rows:
        bind.execute(
            sa.text(
                "UPDATE messages SET shift_id = :shift_id, application_id = :application_id, "
                "booking_id = :booking_id, read_at = :read_at WHERE message_id = :message_id"
            ),
            dict(row),
        )

    with op.batch_alter_table("messages") as batch:
        batch.drop_column("thread_id")
        batch.alter_column("shift_id", existing_type=sa.String(), nullable=False)
        batch.create_check_constraint(
            "ck_messages_context_present",
            "application_id IS NOT NULL OR booking_id IS NOT NULL",
        )
    op.create_index("ix_messages_shift_id", "messages", ["shift_id"])
    op.create_index("ix_messages_application_id", "messages", ["application_id"])
    op.create_index("ix_messages_booking_id", "messages", ["booking_id"])

    op.drop_index("ix_message_read_receipts_party", table_name="message_read_receipts")
    op.drop_table("message_read_receipts")
    op.drop_index("uq_message_thread_participants_active_worker", table_name="message_thread_participants")
    op.drop_index("uq_message_thread_participants_active_user", table_name="message_thread_participants")
    op.drop_index("ix_message_thread_participants_thread", table_name="message_thread_participants")
    op.drop_table("message_thread_participants")
    op.drop_index("uq_message_threads_direct_worker", table_name="message_threads")
    op.drop_index("uq_message_threads_employment", table_name="message_threads")
    op.drop_index("uq_message_threads_shift_group", table_name="message_threads")
    op.drop_index("ix_message_threads_worker", table_name="message_threads")
    op.drop_index("ix_message_threads_venue", table_name="message_threads")
    op.drop_table("message_threads")


def _partial_index(name: str, table: str, columns: list[str], condition: str) -> None:
    where = sa.text(condition)
    if op.get_bind().dialect.name == "postgresql":
        op.create_index(name, table, columns, unique=True, postgresql_where=where)
    else:
        op.create_index(name, table, columns, unique=True, sqlite_where=where)


def _backfill_direct_threads() -> None:
    bind = op.get_bind()
    messages = list(
        bind.execute(
            sa.text(
                "SELECT message_id, shift_id, application_id, booking_id, created_at "
                "FROM messages ORDER BY created_at, message_id"
            )
        ).mappings()
    )
    if not messages:
        return
    applications = {
        row["application_id"]: row
        for row in bind.execute(
            sa.text("SELECT application_id, shift_id, worker_id, booking_id FROM applications")
        ).mappings()
    }
    bookings = {
        row["booking_id"]: row
        for row in bind.execute(
            sa.text("SELECT booking_id, shift_id, worker_id FROM bookings")
        ).mappings()
    }
    shifts = {
        row["shift_id"]: row
        for row in bind.execute(
            sa.text(
                "SELECT s.shift_id, s.venue_id, s.operator_id, s.role, v.name AS venue_name "
                "FROM shifts s LEFT JOIN venues v ON v.venue_id = s.venue_id"
            )
        ).mappings()
    }
    applications_by_party = {(row["shift_id"], row["worker_id"]): row for row in applications.values()}
    bookings_by_party = {(row["shift_id"], row["worker_id"]): row for row in bookings.values()}
    grouped: dict[tuple[str, str], list[sa.RowMapping]] = defaultdict(list)
    message_workers: dict[str, str] = {}
    for message in messages:
        application = applications.get(message["application_id"])
        booking = bookings.get(message["booking_id"])
        worker_id = application["worker_id"] if application else booking["worker_id"] if booking else None
        if worker_id is None:
            raise RuntimeError(f"Message {message['message_id']} has no resolvable worker")
        grouped[(message["shift_id"], worker_id)].append(message)
        message_workers[message["message_id"]] = worker_id

    thread_table = sa.table(
        "message_threads",
        *(sa.column(name) for name in (
            "thread_id", "kind", "venue_id", "shift_id", "application_id", "booking_id",
            "relationship_id", "worker_id", "role_snapshot", "venue_name_snapshot", "created_at",
        )),
    )
    participant_table = sa.table(
        "message_thread_participants",
        *(sa.column(name) for name in (
            "participant_id", "thread_id", "party_kind", "user_id", "worker_id", "joined_at", "left_at",
        )),
    )
    for (shift_id, worker_id), group in grouped.items():
        shift = shifts.get(shift_id)
        if shift is None or shift["venue_id"] is None or shift["venue_name"] is None:
            raise RuntimeError(f"Message thread shift {shift_id} has no venue")
        application = applications_by_party.get((shift_id, worker_id))
        booking = bookings_by_party.get((shift_id, worker_id))
        application_id = application["application_id"] if application else None
        booking_id = booking["booking_id"] if booking else application["booking_id"] if application else None
        thread_id = _stable_id("direct", shift_id, worker_id)
        created_at = group[0]["created_at"]
        bind.execute(
            thread_table.insert().values(
                thread_id=thread_id,
                kind="direct",
                venue_id=shift["venue_id"],
                shift_id=shift_id,
                application_id=application_id,
                booking_id=booking_id,
                relationship_id=None,
                worker_id=worker_id,
                role_snapshot=shift["role"],
                venue_name_snapshot=shift["venue_name"],
                created_at=created_at,
            )
        )
        bind.execute(
            participant_table.insert().values(
                participant_id=_stable_id("participant", thread_id, "worker", worker_id),
                thread_id=thread_id,
                party_kind="worker",
                user_id=None,
                worker_id=worker_id,
                joined_at=created_at,
                left_at=None,
            )
        )
        for message in group:
            bind.execute(
                sa.text("UPDATE messages SET thread_id = :thread_id WHERE message_id = :message_id"),
                {"thread_id": thread_id, "message_id": message["message_id"]},
            )


def _backfill_read_receipts() -> None:
    bind = op.get_bind()
    rows = bind.execute(
        sa.text(
            "SELECT m.message_id, m.sender_role, m.read_at, t.worker_id, s.operator_id "
            "FROM messages m JOIN message_threads t ON t.thread_id = m.thread_id "
            "JOIN shifts s ON s.shift_id = t.shift_id WHERE m.read_at IS NOT NULL"
        )
    ).mappings()
    receipt_table = sa.table(
        "message_read_receipts",
        *(sa.column(name) for name in (
            "receipt_id", "message_id", "party_kind", "user_id", "worker_id", "read_at",
        )),
    )
    for row in rows:
        is_worker_recipient = row["sender_role"] != "worker"
        party_kind = "worker" if is_worker_recipient else "user"
        party_id = row["worker_id"] if is_worker_recipient else row["operator_id"]
        bind.execute(
            receipt_table.insert().values(
                receipt_id=_stable_id("receipt", row["message_id"], party_kind, party_id),
                message_id=row["message_id"],
                party_kind=party_kind,
                user_id=party_id if party_kind == "user" else None,
                worker_id=party_id if party_kind == "worker" else None,
                read_at=row["read_at"],
            )
        )


def _stable_id(*parts: str) -> str:
    return str(uuid5(NAMESPACE_URL, ":".join(parts)))

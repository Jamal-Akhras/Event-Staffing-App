from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal
from uuid import uuid4

import sqlalchemy as sa
from alembic import op

from apps.api.src.config import get_platform_fee_percent

revision = "036"
down_revision = "035"
branch_labels = None
depends_on = None

PENNY = Decimal("0.01")

_BACKFILL = sa.text(
    """
    SELECT b.booking_id, b.shift_id, b.worker_id, b.start_time, b.end_time,
           b.checked_in_at, b.checked_out_at, b.approved_at,
           s.venue_id AS account_id, s.role, s.pay_rate, s.currency,
           w.display_name
    FROM bookings b
    JOIN shifts s ON s.shift_id = b.shift_id
    LEFT JOIN worker_profiles w ON w.worker_id = b.worker_id
    WHERE UPPER(CAST(b.state AS VARCHAR)) IN ('APPROVED', 'PAID') AND s.venue_id IS NOT NULL
    ORDER BY COALESCE(b.approved_at, b.checked_out_at, b.end_time)
    """
)


def _money(value: Decimal) -> Decimal:
    return value.quantize(PENNY, rounding=ROUND_HALF_UP)


def upgrade() -> None:
    op.create_table(
        "booking_charges",
        sa.Column("charge_id", sa.String(), primary_key=True),
        sa.Column("booking_id", sa.String(), nullable=False, unique=True),
        sa.Column("shift_id", sa.String(), nullable=False),
        sa.Column("account_id", sa.String(), nullable=False),
        sa.Column("worker_id", sa.String(), nullable=False),
        sa.Column("worker_name", sa.String(length=160), nullable=False),
        sa.Column("role", sa.String(length=80), nullable=False),
        sa.Column("period", sa.String(length=7), nullable=False),
        sa.Column("start_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("end_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("hours", sa.Numeric(6, 2), nullable=False),
        sa.Column("pay_rate", sa.Numeric(12, 2), nullable=False),
        sa.Column("wages", sa.Numeric(12, 2), nullable=False),
        sa.Column("fee_percent", sa.Numeric(5, 2), nullable=False),
        sa.Column("fee", sa.Numeric(12, 2), nullable=False),
        sa.Column("total", sa.Numeric(12, 2), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.Column("fee_waived", sa.Boolean(), nullable=False),
        sa.Column("waiver_code", sa.String(length=40), nullable=True),
        sa.Column("recorded_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["booking_id"], ["bookings.booking_id"], ondelete="CASCADE"),
        sa.CheckConstraint("hours >= 0", name="ck_booking_charges_hours"),
        sa.CheckConstraint("fee_percent >= 0 AND fee_percent <= 100", name="ck_booking_charges_fee_percent"),
        sa.CheckConstraint("total = wages + fee", name="ck_booking_charges_total"),
    )
    op.create_index("ix_booking_charges_account_period", "booking_charges", ["account_id", "period"])
    op.create_index("ix_booking_charges_account_completed", "booking_charges", ["account_id", "completed_at"])
    op.create_index("ix_booking_charges_worker_completed", "booking_charges", ["worker_id", "completed_at"])
    _backfill()


def _backfill() -> None:
    connection = op.get_bind()
    fee_percent = get_platform_fee_percent()
    waived_by_account: dict[str, int] = {}
    redemptions = {
        row.account_id: row
        for row in connection.execute(
            sa.text("SELECT account_id, code, fee_waived_until, shift_cap FROM partner_code_redemptions")
        )
    }

    for row in connection.execute(_BACKFILL):
        completed = row.approved_at or row.checked_out_at or row.end_time
        start, end = (
            (row.checked_in_at, row.checked_out_at)
            if row.checked_in_at and row.checked_out_at
            else (row.start_time, row.end_time)
        )
        hours = _money(Decimal((end - start).total_seconds()) / Decimal(3600))
        pay_rate = _money(Decimal(row.pay_rate))
        wages = _money(hours * pay_rate)
        redemption = redemptions.get(row.account_id)
        used = waived_by_account.get(row.account_id, 0)
        waived = redemption is not None and completed <= redemption.fee_waived_until and used < redemption.shift_cap
        if waived:
            waived_by_account[row.account_id] = used + 1
        fee = Decimal("0.00") if waived else _money(wages * fee_percent / Decimal(100))
        connection.execute(
            sa.text(
                """
                INSERT INTO booking_charges (
                    charge_id, booking_id, shift_id, account_id, worker_id, worker_name, role, period,
                    start_time, end_time, completed_at, hours, pay_rate, wages, fee_percent, fee, total,
                    currency, fee_waived, waiver_code, recorded_at
                ) VALUES (
                    :charge_id, :booking_id, :shift_id, :account_id, :worker_id, :worker_name, :role, :period,
                    :start_time, :end_time, :completed_at, :hours, :pay_rate, :wages, :fee_percent, :fee, :total,
                    :currency, :fee_waived, :waiver_code, :recorded_at
                )
                """
            ),
            {
                "charge_id": str(uuid4()),
                "booking_id": row.booking_id,
                "shift_id": row.shift_id,
                "account_id": row.account_id,
                "worker_id": row.worker_id,
                "worker_name": row.display_name or "Worker",
                "role": row.role,
                "period": completed.strftime("%Y-%m"),
                "start_time": row.start_time,
                "end_time": row.end_time,
                "completed_at": completed,
                "hours": hours,
                "pay_rate": pay_rate,
                "wages": wages,
                "fee_percent": fee_percent,
                "fee": fee,
                "total": _money(wages + fee),
                "currency": row.currency or "GBP",
                "fee_waived": waived,
                "waiver_code": redemption.code if waived else None,
                "recorded_at": completed,
            },
        )


def downgrade() -> None:
    op.drop_table("booking_charges")

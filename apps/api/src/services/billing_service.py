from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import ROUND_HALF_UP, Decimal
from uuid import uuid4

from dateutil.relativedelta import relativedelta

from apps.api.src.models.partner_code import PartnerCode, PartnerCodeRedemption
from apps.api.src.repositories.booking_repository import BookingRepository
from apps.api.src.repositories.partner_code_repository import PartnerCodeRepository
from apps.api.src.repositories.shift_repository import ShiftRepository
from apps.api.src.repositories.worker_profile_repository import WorkerProfileRepository
from apps.api.src.services.errors import ConflictError, NotFoundError, ValidationError
from packages.domain.src.booking import Booking
from packages.domain.src.booking_state import BookingState

COMPLETED_STATES = {BookingState.APPROVED, BookingState.PAID}
PENNY = Decimal("0.01")
FOUNDING_WAIVER_MONTHS = 3
FOUNDING_SHIFT_CAP = 20


@dataclass(frozen=True)
class BillingLine:
    booking_id: str
    shift_id: str
    worker_id: str
    worker_name: str
    role: str
    start_time: datetime
    end_time: datetime
    completed_at: datetime
    hours: Decimal
    wages: Decimal
    fee: Decimal
    total: Decimal
    waived: bool
    state: str


@dataclass(frozen=True)
class Waiver:
    code: str
    label: str
    fee_waived_until: datetime
    shift_cap: int
    shifts_used: int
    active: bool
    waived_booking_ids: frozenset[str]


@dataclass(frozen=True)
class BillingSummary:
    month: str
    fee_percent: Decimal
    plan: str
    waiver: Waiver | None
    lines: list[BillingLine]
    wages_total: Decimal
    fee_total: Decimal
    grand_total: Decimal
    completed_shifts_all_time: int


class BillingService:
    def __init__(
        self,
        bookings: BookingRepository,
        shifts: ShiftRepository,
        workers: WorkerProfileRepository,
        partner_codes: PartnerCodeRepository,
        fee_percent: Decimal,
    ) -> None:
        self._bookings = bookings
        self._shifts = shifts
        self._workers = workers
        self._codes = partner_codes
        self._fee_percent = fee_percent

    def summary(self, account_id: str, month: str, now: datetime) -> BillingSummary:
        completed = sorted(
            (b for b in self._bookings.list_for_account(account_id, limit=10_000) if b.state in COMPLETED_STATES),
            key=completed_at,
        )
        waiver = self._waiver(account_id, completed, now)
        waived_ids = waiver.waived_booking_ids if waiver else frozenset()
        lines = [self._line(b, b.booking_id in waived_ids) for b in completed if completed_at(b).strftime("%Y-%m") == month]
        wages_total = money(sum((line.wages for line in lines), Decimal(0)))
        fee_total = money(sum((line.fee for line in lines), Decimal(0)))
        return BillingSummary(
            month=month,
            fee_percent=self._fee_percent,
            plan="founding_partner" if waiver and waiver.active else "standard",
            waiver=waiver,
            lines=lines,
            wages_total=wages_total,
            fee_total=fee_total,
            grand_total=money(wages_total + fee_total),
            completed_shifts_all_time=len(completed),
        )

    def redeem(self, raw_code: str, account_id: str, user_id: str, now: datetime) -> Waiver:
        code = self._codes.get_code_for_redemption(raw_code.strip().upper(), account_id)
        if code is None:
            raise NotFoundError("That code isn't valid.")
        if code.expires_at is not None and now > code.expires_at:
            raise ValidationError("That code has expired.")
        if self._codes.get_redemption_for_account(account_id) is not None:
            raise ConflictError("This venue already has a partner code applied.")
        if len(self._codes.list_redemptions(code.code)) >= code.max_redemptions:
            raise ConflictError("That code has already been used.")
        self._codes.save_redemption(
            PartnerCodeRedemption(
                redemption_id=str(uuid4()),
                code=code.code,
                account_id=account_id,
                redeemed_at=now,
                redeemed_by_user_id=user_id,
                fee_waived_until=now + relativedelta(months=code.waiver_months),
                shift_cap=code.shift_cap,
            )
        )
        return self.summary(account_id, now.strftime("%Y-%m"), now).waiver

    def _waiver(self, account_id: str, completed: list[Booking], now: datetime) -> Waiver | None:
        redemption = self._codes.get_redemption_for_account(account_id)
        if redemption is None:
            return None
        code = self._codes.get_code(redemption.code)
        if code is None:
            return None
        eligible = [b for b in completed if redemption.redeemed_at <= completed_at(b) <= redemption.fee_waived_until]
        waived = eligible[: redemption.shift_cap]
        return Waiver(
            code=code.code,
            label=code.label,
            fee_waived_until=redemption.fee_waived_until,
            shift_cap=redemption.shift_cap,
            shifts_used=len(waived),
            active=now <= redemption.fee_waived_until and len(waived) < redemption.shift_cap,
            waived_booking_ids=frozenset(b.booking_id for b in waived),
        )

    def _line(self, booking: Booking, waived: bool) -> BillingLine:
        shift = self._shifts.get(booking.shift_id)
        if shift is None:
            raise NotFoundError(f"Shift {booking.shift_id} is missing for booking {booking.booking_id}.")
        worker = self._workers.get(booking.worker_id)
        hours = worked_hours(booking)
        wages = money(hours * Decimal(shift.pay_rate))
        fee = Decimal("0.00") if waived else money(wages * self._fee_percent / Decimal(100))
        return BillingLine(
            booking_id=booking.booking_id,
            shift_id=shift.shift_id,
            worker_id=booking.worker_id,
            worker_name=worker.display_name if worker and worker.display_name else "Worker",
            role=shift.role,
            start_time=booking.start_time,
            end_time=booking.end_time,
            completed_at=completed_at(booking),
            hours=hours,
            wages=wages,
            fee=fee,
            total=money(wages + fee),
            waived=waived,
            state=booking.state.value,
        )


def completed_at(booking: Booking) -> datetime:
    return booking.approved_at or booking.checked_out_at or booking.end_time


def worked_hours(booking: Booking) -> Decimal:
    if booking.checked_in_at and booking.checked_out_at:
        start, end = booking.checked_in_at, booking.checked_out_at
    else:
        start, end = booking.start_time, booking.end_time
    return (Decimal((end - start).total_seconds()) / Decimal(3600)).quantize(PENNY, rounding=ROUND_HALF_UP)


def money(value: Decimal) -> Decimal:
    return value.quantize(PENNY, rounding=ROUND_HALF_UP)


def new_partner_code(prefix: str, label: str, max_redemptions: int, created_by: str, now: datetime, expires_at: datetime | None) -> PartnerCode:
    import secrets

    normalized_prefix = prefix.strip().upper()
    if not normalized_prefix or len(normalized_prefix) > 21 or not normalized_prefix.isalnum():
        raise ValueError("prefix must contain 1-21 letters or numbers")
    if not label.strip() or len(label) > 160:
        raise ValueError("label must contain 1-160 characters")
    if max_redemptions < 1:
        raise ValueError("max redemptions must be positive")
    if expires_at is not None and expires_at <= now:
        raise ValueError("redemption expiry must be in the future")
    alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
    body = "".join(secrets.choice(alphabet) for _ in range(8))
    return PartnerCode(
        code=f"{normalized_prefix}-{body[:4]}-{body[4:]}",
        label=label.strip(),
        waiver_months=FOUNDING_WAIVER_MONTHS,
        shift_cap=FOUNDING_SHIFT_CAP,
        max_redemptions=max_redemptions,
        created_at=now,
        created_by=created_by,
        expires_at=expires_at,
    )

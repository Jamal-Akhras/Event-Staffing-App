from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from uuid import uuid4

from dateutil.relativedelta import relativedelta

from apps.api.src.models.booking_charge import BookingCharge
from apps.api.src.models.partner_code import PartnerCode, PartnerCodeRedemption
from apps.api.src.repositories.booking_charge_repository import BookingChargeRepository
from apps.api.src.repositories.booking_repository import BookingRepository
from apps.api.src.repositories.partner_code_repository import PartnerCodeRepository
from apps.api.src.services.billing_math import money
from apps.api.src.services.code_generation import new_code
from apps.api.src.services.errors import ConflictError, NotFoundError, ValidationError

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
        charges: BookingChargeRepository,
        partner_codes: PartnerCodeRepository,
        fee_percent: Decimal,
    ) -> None:
        self._bookings = bookings
        self._charges = charges
        self._codes = partner_codes
        self._fee_percent = fee_percent

    def summary(self, account_id: str, month: str, now: datetime) -> BillingSummary:
        charges = self._charges.list_for_account(account_id)
        waiver = self._waiver(account_id, charges, now)
        lines = [self._line(charge) for charge in charges if charge.period == month]
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
            completed_shifts_all_time=len(charges),
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

    def _waiver(self, account_id: str, charges: list[BookingCharge], now: datetime) -> Waiver | None:
        redemption = self._codes.get_redemption_for_account(account_id)
        if redemption is None:
            return None
        code = self._codes.get_code(redemption.code)
        if code is None:
            return None
        waived = [charge for charge in charges if charge.fee_waived]
        return Waiver(
            code=code.code,
            label=code.label,
            fee_waived_until=redemption.fee_waived_until,
            shift_cap=redemption.shift_cap,
            shifts_used=len(waived),
            active=now <= redemption.fee_waived_until and len(waived) < redemption.shift_cap,
            waived_booking_ids=frozenset(charge.booking_id for charge in waived),
        )

    def _line(self, charge: BookingCharge) -> BillingLine:
        booking = self._bookings.get(charge.booking_id)
        if booking is None:
            raise NotFoundError(f"Booking {charge.booking_id} is missing for charge {charge.charge_id}.")
        return BillingLine(
            booking_id=charge.booking_id,
            shift_id=charge.shift_id,
            worker_id=charge.worker_id,
            worker_name=charge.worker_name,
            role=charge.role,
            start_time=charge.start_time,
            end_time=charge.end_time,
            completed_at=charge.completed_at,
            hours=charge.hours,
            wages=charge.wages,
            fee=charge.fee,
            total=charge.total,
            waived=charge.fee_waived,
            state=booking.state.value,
        )


def new_partner_code(prefix: str, label: str, max_redemptions: int, created_by: str, now: datetime, expires_at: datetime | None) -> PartnerCode:
    if not label.strip() or len(label) > 160:
        raise ValueError("label must contain 1-160 characters")
    if max_redemptions < 1:
        raise ValueError("max redemptions must be positive")
    if expires_at is not None and expires_at <= now:
        raise ValueError("redemption expiry must be in the future")
    return PartnerCode(
        code=new_code(prefix),
        label=label.strip(),
        waiver_months=FOUNDING_WAIVER_MONTHS,
        shift_cap=FOUNDING_SHIFT_CAP,
        max_redemptions=max_redemptions,
        created_at=now,
        created_by=created_by,
        expires_at=expires_at,
    )

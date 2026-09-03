from __future__ import annotations

import csv
import io
from dataclasses import dataclass, replace
from datetime import date, datetime
from decimal import ROUND_HALF_UP, Decimal
from typing import Any
from uuid import uuid4

from apps.api.src.models.booking_charge import BookingCharge
from apps.api.src.models.booking_charge_adjustment import BookingChargeAdjustment
from apps.api.src.models.booking_transition import BookingTransition
from apps.api.src.repositories.account_repository import AccountRepository
from apps.api.src.repositories.booking_charge_adjustment_repository import (
    BookingChargeAdjustmentRepository,
)
from apps.api.src.repositories.booking_charge_repository import BookingChargeRepository
from apps.api.src.repositories.booking_repository import BookingRepository
from apps.api.src.repositories.booking_transition_repository import BookingTransitionRepository
from apps.api.src.repositories.market_repository import MarketRepository
from apps.api.src.repositories.shift_repository import ShiftRepository
from apps.api.src.repositories.worker_profile_repository import WorkerProfileRepository
from apps.api.src.repositories.worker_relationship_repository import WorkerRelationshipRepository
from apps.api.src.services.billing_math import PENNY, money, worked_hours
from apps.api.src.services.errors import NotFoundError, ValidationError
from apps.api.src.services.rota_week import local_day, venue_timezone, week_window
from packages.domain.src.booking import Booking
from packages.domain.src.booking_state import BookingState
from packages.domain.src.booking_state_machine import TransitionError

VIEW_STATES = (
    BookingState.CONFIRMED,
    BookingState.CHECKED_IN,
    BookingState.CHECKED_OUT,
    BookingState.APPROVED,
    BookingState.PAID,
)
ZERO = Decimal("0.00")


@dataclass(frozen=True)
class TimesheetRow:
    day: date
    booking: Booking
    charge_id: str | None
    shift_role: str
    scheduled_hours: Decimal
    worked: Decimal | None
    hours_source: str
    approved_hours: Decimal | None
    approved_wages: Decimal | None
    adjustments_total_hours: Decimal


@dataclass(frozen=True)
class TimesheetWorker:
    worker_id: str
    display_name: str
    relationship_type: str
    contracted_hours_per_week: Decimal | None
    rows: list[TimesheetRow]
    scheduled_hours: Decimal
    worked_hours: Decimal
    approved_hours: Decimal


@dataclass(frozen=True)
class TimesheetWeek:
    venue_id: str
    week_start: date
    workers: list[TimesheetWorker]
    total_scheduled_hours: Decimal
    total_worked_hours: Decimal
    total_approved_hours: Decimal
    total_approved_wages: Decimal


class TimesheetService:
    def __init__(
        self,
        shifts: ShiftRepository,
        bookings: BookingRepository,
        workers: WorkerProfileRepository,
        relationships: WorkerRelationshipRepository,
        charges: BookingChargeRepository,
        adjustments: BookingChargeAdjustmentRepository,
        transitions: BookingTransitionRepository,
        accounts: AccountRepository,
        markets: MarketRepository,
    ) -> None:
        self._shifts = shifts
        self._bookings = bookings
        self._workers = workers
        self._relationships = relationships
        self._charges = charges
        self._adjustments = adjustments
        self._transitions = transitions
        self._accounts = accounts
        self._markets = markets

    def week_view(self, venue_id: str, week_start: date) -> TimesheetWeek:
        zone = venue_timezone(venue_id, self._accounts, self._markets)
        window_start, window_end = week_window(week_start, zone)
        shifts = {
            shift.shift_id: shift
            for shift in self._shifts.list_in_range(venue_id, window_start, window_end)
        }
        bookings = [
            b for b in self._bookings.list_for_shifts(list(shifts)) if b.state in VIEW_STATES
        ]
        relationships = {
            r.worker_id: r for r in self._relationships.list_for_venue(venue_id)
        }
        charges = {c.booking_id: c for c in self._charges.list_for_account(venue_id)}
        adjustments_by_charge: dict[str, list[BookingChargeAdjustment]] = {}
        for adjustment in self._adjustments.list_for_charges(
            [c.charge_id for c in charges.values()]
        ):
            adjustments_by_charge.setdefault(adjustment.charge_id, []).append(adjustment)
        names = {
            p.worker_id: p.display_name
            for p in self._workers.list_by_ids(sorted({b.worker_id for b in bookings}))
        }

        by_worker: dict[str, list[TimesheetRow]] = {}
        for booking in sorted(bookings, key=lambda b: b.start_time):
            shift = shifts[booking.shift_id]
            charge = charges.get(booking.booking_id)
            row = self._row(booking, shift.role, charge, adjustments_by_charge, zone)
            by_worker.setdefault(booking.worker_id, []).append(row)

        workers = []
        for worker_id in sorted(by_worker):
            rows = by_worker[worker_id]
            relationship = relationships.get(worker_id)
            scheduled = sum((r.scheduled_hours for r in rows), ZERO)
            worked = sum((r.worked or ZERO for r in rows), ZERO)
            approved = sum((r.approved_hours or ZERO for r in rows), ZERO)
            workers.append(
                TimesheetWorker(
                    worker_id=worker_id,
                    display_name=names.get(worker_id, "Worker"),
                    relationship_type=relationship.relationship_type if relationship else "one_off",
                    contracted_hours_per_week=(
                        relationship.contracted_hours_per_week if relationship else None
                    ),
                    rows=rows,
                    scheduled_hours=scheduled,
                    worked_hours=worked,
                    approved_hours=approved,
                )
            )

        return TimesheetWeek(
            venue_id=venue_id,
            week_start=week_start,
            workers=workers,
            total_scheduled_hours=sum((w.scheduled_hours for w in workers), ZERO),
            total_worked_hours=sum((w.worked_hours for w in workers), ZERO),
            total_approved_hours=sum((w.approved_hours for w in workers), ZERO),
            total_approved_wages=sum(
                (r.approved_wages for w in workers for r in w.rows if r.approved_wages is not None),
                ZERO,
            ),
        )

    def adjust_hours(
        self, venue_id: str, booking_id: str, checked_in_at: datetime, checked_out_at: datetime,
        reason: str, actor_user_id: str, now: datetime,
    ) -> Booking:
        booking = self._venue_booking(venue_id, booking_id)
        if self._charges.get_for_booking(booking_id) is not None:
            raise ValidationError("These hours are already approved: correct the charge instead.")
        if booking.state != BookingState.CHECKED_OUT:
            raise ValidationError("Hours can only be adjusted once the shift is checked out.")
        if checked_out_at <= checked_in_at:
            raise ValidationError("Check-out must be after check-in.")
        before = worked_hours(booking)
        updated = self._bookings.save(
            replace(booking, override_checked_in_at=checked_in_at, override_checked_out_at=checked_out_at)
        )
        self._transitions.append(
            BookingTransition(
                transition_id=str(uuid4()),
                booking_id=booking_id,
                from_state="checked_out",
                to_state="checked_out",
                occurred_at=now,
                actor_user_id=actor_user_id,
                actor_role="operator",
                reason_code="hours_adjusted",
                reason_note=reason,
                context={
                    "previous_hours": str(before),
                    "hours": str(worked_hours(updated)),
                    "checked_in_at": checked_in_at.isoformat(),
                    "checked_out_at": checked_out_at.isoformat(),
                },
            )
        )
        return updated

    def record_attendance(
        self, venue_id: str, booking_id: str, checked_in_at: datetime, checked_out_at: datetime,
        actor_user_id: str, now: datetime,
    ) -> Booking:
        booking = self._venue_booking(venue_id, booking_id)
        if booking.attendance_mode != "employed":
            raise ValidationError(
                "Attendance can only be recorded for employed staff. Temps use the two-party codes."
            )
        try:
            updated = self._bookings.save(booking.record_attendance(checked_in_at, checked_out_at))
        except TransitionError as exc:
            raise ValidationError(str(exc)) from exc
        self._transitions.append(
            BookingTransition(
                transition_id=str(uuid4()),
                booking_id=booking_id,
                from_state="confirmed",
                to_state="checked_out",
                occurred_at=now,
                actor_user_id=actor_user_id,
                actor_role="operator",
                reason_code="venue_recorded",
                context={
                    "checked_in_at": checked_in_at.isoformat(),
                    "checked_out_at": checked_out_at.isoformat(),
                },
            )
        )
        return updated

    def correct_charge(
        self, venue_id: str, charge_id: str, delta_hours: Decimal, reason: str,
        actor_user_id: str, now: datetime,
    ) -> BookingChargeAdjustment:
        if delta_hours == 0:
            raise ValidationError("A correction has to change the hours.")
        charge = next(
            (c for c in self._charges.list_for_account(venue_id) if c.charge_id == charge_id), None
        )
        if charge is None:
            raise NotFoundError("That charge was not found.")
        existing = self._adjustments.list_for_charge(charge_id)
        total_hours = charge.hours + sum((a.delta_hours for a in existing), ZERO) + delta_hours
        if total_hours < 0:
            raise ValidationError("That correction would take the total hours below zero.")
        delta_wages = money(delta_hours * charge.pay_rate)
        if charge.fee_waived or charge.fee_percent == 0:
            delta_fee = ZERO
        else:
            delta_fee = money(delta_wages * charge.fee_percent / Decimal(100))
        return self._adjustments.record(
            BookingChargeAdjustment(
                adjustment_id=str(uuid4()),
                charge_id=charge_id,
                booking_id=charge.booking_id,
                delta_hours=delta_hours,
                delta_wages=delta_wages,
                delta_fee=delta_fee,
                reason=reason,
                created_by_user_id=actor_user_id,
                created_at=now,
            )
        )

    def csv_for_week(self, venue_id: str, week_start: date) -> str:
        zone = venue_timezone(venue_id, self._accounts, self._markets)
        window_start, window_end = week_window(week_start, zone)
        charges = [
            c
            for c in self._charges.list_for_account(venue_id)
            if window_start <= c.start_time < window_end
        ]
        adjustments = self._adjustments.list_for_charges([c.charge_id for c in charges])

        buffer = io.StringIO()
        writer = csv.writer(buffer, lineterminator="\n")
        writer.writerow(
            ["worker_id", "worker_name", "relationship", "role", "date", "start", "end",
             "hours", "hours_source", "rate", "wages", "adjustment_ref", "currency", "booking_id"]
        )
        for charge in sorted(charges, key=lambda c: (c.start_time, c.worker_id)):
            booking = self._bookings.get(charge.booking_id)
            writer.writerow(_charge_row(charge, booking, zone))
            for adjustment in [a for a in adjustments if a.charge_id == charge.charge_id]:
                writer.writerow(_adjustment_row(charge, adjustment, zone))
        return buffer.getvalue()

    def _venue_booking(self, venue_id: str, booking_id: str) -> Booking:
        booking = self._bookings.get(booking_id)
        if booking is None:
            raise NotFoundError("That booking was not found.")
        shift = self._shifts.get(booking.shift_id)
        if shift is None or shift.account_id != venue_id:
            raise NotFoundError("That booking was not found.")
        return booking

    def _row(
        self, booking: Booking, role: str, charge: BookingCharge | None,
        adjustments_by_charge: dict[str, list[BookingChargeAdjustment]], zone,
    ) -> TimesheetRow:
        scheduled = _hours_between(booking.start_time, booking.end_time)
        clocked = (
            worked_hours(booking)
            if booking.checked_in_at is not None and booking.checked_out_at is not None
            else None
        )
        adjustment_hours = ZERO
        approved_hours = approved_wages = None
        source = "scheduled"
        if booking.override_checked_in_at is not None:
            source = "adjusted"
        elif clocked is not None:
            source = "clocked"
        if charge is not None:
            deltas = adjustments_by_charge.get(charge.charge_id, [])
            adjustment_hours = sum((a.delta_hours for a in deltas), ZERO)
            approved_hours = charge.hours + adjustment_hours
            approved_wages = charge.wages + sum((a.delta_wages for a in deltas), ZERO)
            source = "approved"
        return TimesheetRow(
            day=local_day(booking.start_time, zone),
            booking=booking,
            charge_id=charge.charge_id if charge is not None else None,
            shift_role=role,
            scheduled_hours=scheduled,
            worked=clocked,
            hours_source=source,
            approved_hours=approved_hours,
            approved_wages=approved_wages,
            adjustments_total_hours=adjustment_hours,
        )


def _hours_between(start: datetime, end: datetime) -> Decimal:
    return Decimal((end - start).total_seconds() / 3600).quantize(PENNY, rounding=ROUND_HALF_UP)


def _escape(value: Any) -> str:
    text = str(value)
    if text and text[0] in ("=", "+", "-", "@"):
        return "'" + text
    return text


def _charge_row(charge: BookingCharge, booking: Booking | None, zone) -> list[str]:
    source = "scheduled"
    if booking is not None and booking.override_checked_in_at is not None:
        source = "adjusted"
    elif booking is not None and booking.checked_in_at is not None:
        source = "clocked"
    return [
        _escape(charge.worker_id),
        _escape(charge.worker_name),
        _escape(charge.worker_relationship or "one_off"),
        _escape(charge.role),
        str(local_day(charge.start_time, zone)),
        charge.start_time.astimezone(zone).strftime("%H:%M"),
        charge.end_time.astimezone(zone).strftime("%H:%M"),
        str(charge.hours),
        source,
        str(charge.pay_rate),
        str(charge.wages),
        "",
        charge.currency,
        charge.booking_id,
    ]


def _adjustment_row(charge: BookingCharge, adjustment: BookingChargeAdjustment, zone) -> list[str]:
    return [
        _escape(charge.worker_id),
        _escape(charge.worker_name),
        _escape(charge.worker_relationship or "one_off"),
        _escape(charge.role),
        str(local_day(charge.start_time, zone)),
        "",
        "",
        _escape(str(adjustment.delta_hours)),
        "correction",
        str(charge.pay_rate),
        _escape(str(adjustment.delta_wages)),
        adjustment.adjustment_id,
        charge.currency,
        charge.booking_id,
    ]

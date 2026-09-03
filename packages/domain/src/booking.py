from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import datetime, timedelta

from packages.domain.src.attendance import new_attendance_code
from packages.domain.src.booking_state import BookingState
from packages.domain.src.booking_state_machine import TransitionError, require_transition


CHECK_IN_OPEN_MINUTES = 30
CHECK_IN_CLOSE_MINUTES = 15


@dataclass(frozen=True)
class Booking:
    booking_id: str
    shift_id: str
    worker_id: str
    operator_id: str
    start_time: datetime
    end_time: datetime
    state: BookingState = BookingState.REQUESTED
    created_at: datetime | None = None
    confirmed_at: datetime | None = None
    checked_in_at: datetime | None = None
    checked_out_at: datetime | None = None
    approved_at: datetime | None = None
    paid_at: datetime | None = None
    cancelled_at: datetime | None = None
    cancellation_reason: str | None = None
    cancelled_by_user_id: str | None = None
    no_show_at: datetime | None = None
    payment_method: str | None = None
    payment_reference: str | None = None
    payment_recorded_by_user_id: str | None = None
    check_in_code: str = field(default_factory=new_attendance_code)
    completion_code: str = field(default_factory=new_attendance_code)
    attendance_mode: str = "pin"
    override_checked_in_at: datetime | None = None
    override_checked_out_at: datetime | None = None

    def __post_init__(self) -> None:
        if self.completion_code == self.check_in_code:
            object.__setattr__(self, "completion_code", new_attendance_code(self.check_in_code))

    def transition_to(self, target: BookingState, now: datetime) -> "Booking":
        if target == self.state:
            return self

        require_transition(self.state, target)

        if target == BookingState.CHECKED_IN:
            if not _within_check_in_window(now, self.start_time):
                raise TransitionError("Check-in is outside the allowed time window.")
            return replace(self, state=target, checked_in_at=now)

        if target == BookingState.CHECKED_OUT:
            if self.checked_in_at is None:
                raise TransitionError("Cannot check out before check-in.")
            return replace(self, state=target, checked_out_at=now)

        if target == BookingState.APPROVED:
            if self.checked_out_at is None:
                raise TransitionError("Cannot approve before check-out.")
            return replace(self, state=target, approved_at=now)

        if target == BookingState.PAID:
            if self.approved_at is None:
                raise TransitionError("Cannot pay before approval.")
            return replace(self, state=target, paid_at=now)

        if target == BookingState.NO_SHOW:
            if not _check_in_window_expired(now, self.start_time):
                raise TransitionError("Cannot mark no-show before check-in window closes.")
            return replace(self, state=target, no_show_at=now)

        if target == BookingState.CANCELLED_BY_WORKER:
            if now >= self.start_time:
                raise TransitionError("Worker cancellations must be before start time.")
            return replace(self, state=target, cancelled_at=now)

        if target == BookingState.CANCELLED_BY_OPERATOR:
            if now >= self.start_time:
                raise TransitionError("Venue cancellations must be before start time.")
            return replace(self, state=target, cancelled_at=now)

        return replace(self, state=target, confirmed_at=now)

    def record_attendance(self, checked_in_at: datetime, checked_out_at: datetime) -> "Booking":
        if self.state != BookingState.CONFIRMED:
            raise TransitionError("Attendance can only be recorded on a confirmed booking.")
        if checked_out_at <= checked_in_at:
            raise TransitionError("Check-out must be after check-in.")
        return replace(
            self,
            state=BookingState.CHECKED_OUT,
            checked_in_at=checked_in_at,
            checked_out_at=checked_out_at,
        )


def _within_check_in_window(now: datetime, start_time: datetime) -> bool:
    window_open = start_time - timedelta(minutes=CHECK_IN_OPEN_MINUTES)
    window_close = start_time + timedelta(minutes=CHECK_IN_CLOSE_MINUTES)
    return window_open <= now <= window_close


def _check_in_window_expired(now: datetime, start_time: datetime) -> bool:
    window_close = start_time + timedelta(minutes=CHECK_IN_CLOSE_MINUTES)
    return now > window_close

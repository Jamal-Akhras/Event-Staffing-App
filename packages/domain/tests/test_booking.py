from datetime import datetime, timedelta

import pytest

from packages.domain.src.booking import Booking
from packages.domain.src.booking_state import BookingState
from packages.domain.src.booking_state_machine import TransitionError


def _base_booking(start_offset_minutes: int = 60) -> Booking:
    now = datetime(2030, 1, 1, 12, 0, 0)
    start = now + timedelta(minutes=start_offset_minutes)
    end = start + timedelta(hours=4)
    return Booking(
        booking_id="b-1",
        shift_id="s-1",
        worker_id="w-1",
        operator_id="o-1",
        start_time=start,
        end_time=end,
        created_at=now,
    )


def test_confirm_sets_timestamp():
    booking = _base_booking()
    now = booking.created_at + timedelta(minutes=5)
    updated = booking.transition_to(BookingState.CONFIRMED, now)
    assert updated.state == BookingState.CONFIRMED
    assert updated.confirmed_at == now


def test_check_in_window_enforced():
    booking = _base_booking().transition_to(BookingState.CONFIRMED, datetime(2030, 1, 1, 12, 5, 0))
    too_early = booking.start_time - timedelta(minutes=31)
    with pytest.raises(TransitionError):
        booking.transition_to(BookingState.CHECKED_IN, too_early)

    within = booking.start_time - timedelta(minutes=10)
    checked_in = booking.transition_to(BookingState.CHECKED_IN, within)
    assert checked_in.checked_in_at == within


def test_check_in_window_boundaries():
    booking = _base_booking().transition_to(BookingState.CONFIRMED, datetime(2030, 1, 1, 12, 5, 0))
    at_open = booking.start_time - timedelta(minutes=30)
    at_close = booking.start_time + timedelta(minutes=15)
    assert booking.transition_to(BookingState.CHECKED_IN, at_open).checked_in_at == at_open
    assert booking.transition_to(BookingState.CHECKED_IN, at_close).checked_in_at == at_close


def test_check_out_requires_check_in():
    booking = _base_booking().transition_to(BookingState.CONFIRMED, datetime(2030, 1, 1, 12, 5, 0))
    with pytest.raises(TransitionError):
        booking.transition_to(BookingState.CHECKED_OUT, booking.start_time + timedelta(hours=1))


def test_no_show_requires_window_expired():
    booking = _base_booking().transition_to(BookingState.CONFIRMED, datetime(2030, 1, 1, 12, 5, 0))
    before_close = booking.start_time + timedelta(minutes=10)
    with pytest.raises(TransitionError):
        booking.transition_to(BookingState.NO_SHOW, before_close)

    after_close = booking.start_time + timedelta(minutes=16)
    updated = booking.transition_to(BookingState.NO_SHOW, after_close)
    assert updated.no_show_at == after_close


def test_no_show_requires_confirmed():
    booking = _base_booking()
    after_close = booking.start_time + timedelta(minutes=16)
    with pytest.raises(TransitionError):
        booking.transition_to(BookingState.NO_SHOW, after_close)


def test_worker_cancel_requires_before_start():
    booking = _base_booking().transition_to(BookingState.CONFIRMED, datetime(2030, 1, 1, 12, 5, 0))
    after_start = booking.start_time + timedelta(minutes=1)
    with pytest.raises(TransitionError):
        booking.transition_to(BookingState.CANCELLED_BY_WORKER, after_start)


def test_operator_cancel_allowed_after_start():
    booking = _base_booking().transition_to(BookingState.CONFIRMED, datetime(2030, 1, 1, 12, 5, 0))
    after_start = booking.start_time + timedelta(minutes=1)
    updated = booking.transition_to(BookingState.CANCELLED_BY_OPERATOR, after_start)
    assert updated.state == BookingState.CANCELLED_BY_OPERATOR


def test_paid_requires_approved():
    booking = _base_booking().transition_to(BookingState.CONFIRMED, datetime(2030, 1, 1, 12, 5, 0))
    with pytest.raises(TransitionError):
        booking.transition_to(BookingState.PAID, booking.start_time)


def test_idempotent_same_state():
    booking = _base_booking()
    assert booking.transition_to(BookingState.REQUESTED, booking.created_at) is booking

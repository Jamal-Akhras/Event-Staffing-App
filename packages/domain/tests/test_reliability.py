from datetime import datetime, timedelta

from packages.domain.src.booking import Booking
from packages.domain.src.booking_state import BookingState
from packages.domain.src.reliability import compute_reliability


def _booking(state: BookingState) -> Booking:
    now = datetime(2030, 1, 1, 12, 0, 0)
    return Booking(
        booking_id=f"booking-{state.value}",
        shift_id="shift-1",
        worker_id="worker-1",
        operator_id="operator-1",
        start_time=now + timedelta(hours=1),
        end_time=now + timedelta(hours=5),
        state=state,
        created_at=now,
    )


def test_reliability_empty_returns_zero():
    assert compute_reliability([]) == 0.0


def test_reliability_completed_only():
    bookings = [
        _booking(BookingState.CHECKED_OUT),
        _booking(BookingState.APPROVED),
    ]
    assert compute_reliability(bookings) == 1.0


def test_reliability_mixed_outcomes():
    bookings = [
        _booking(BookingState.CHECKED_OUT),
        _booking(BookingState.NO_SHOW),
        _booking(BookingState.CANCELLED_BY_WORKER),
    ]
    assert compute_reliability(bookings) == 1 / 3

import pytest

from packages.domain.src.booking_state import BookingState
from packages.domain.src.booking_state_machine import (
    TransitionError,
    allowed_next_states,
    is_valid_transition,
    require_transition,
)

def test_paid_is_terminal():
    assert allowed_next_states(BookingState.PAID) == set()

def test_allowed_transitions():
    assert is_valid_transition(BookingState.REQUESTED, BookingState.CONFIRMED)
    assert is_valid_transition(BookingState.CONFIRMED, BookingState.CHECKED_IN)
    assert is_valid_transition(BookingState.CHECKED_IN, BookingState.CHECKED_OUT)
    assert is_valid_transition(BookingState.CHECKED_OUT, BookingState.APPROVED)
    assert is_valid_transition(BookingState.APPROVED, BookingState.PAID)
    assert is_valid_transition(BookingState.CONFIRMED, BookingState.NO_SHOW)

def test_no_show_only_from_confirmed():
    assert BookingState.NO_SHOW in allowed_next_states(BookingState.CONFIRMED)
    assert BookingState.NO_SHOW not in allowed_next_states(BookingState.REQUESTED)


def test_cancel_is_allowed_only_before_work_starts():
    for state in [BookingState.REQUESTED, BookingState.CONFIRMED]:
        assert BookingState.CANCELLED_BY_WORKER in allowed_next_states(state)
        assert BookingState.CANCELLED_BY_OPERATOR in allowed_next_states(state)

    for state in [
        BookingState.CHECKED_IN,
        BookingState.CHECKED_OUT,
        BookingState.APPROVED,
        BookingState.PAID,
        BookingState.NO_SHOW,
        BookingState.CANCELLED_BY_WORKER,
        BookingState.CANCELLED_BY_OPERATOR,
    ]:
        assert BookingState.CANCELLED_BY_WORKER not in allowed_next_states(state)
        assert BookingState.CANCELLED_BY_OPERATOR not in allowed_next_states(state)


def test_cancel_not_allowed_from_paid():
    assert BookingState.CANCELLED_BY_WORKER not in allowed_next_states(BookingState.PAID)


def test_invalid_transition_raises():
    with pytest.raises(TransitionError):
        require_transition(BookingState.REQUESTED, BookingState.CHECKED_IN)

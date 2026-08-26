from __future__ import annotations

from packages.domain.src.booking_state import BookingState


class TransitionError(ValueError):
    pass


_NEXT: dict[BookingState, set[BookingState]] = {
    BookingState.REQUESTED: {BookingState.CONFIRMED},
    BookingState.CONFIRMED: {BookingState.CHECKED_IN, BookingState.NO_SHOW},
    BookingState.CHECKED_IN: {BookingState.CHECKED_OUT},
    BookingState.CHECKED_OUT: {BookingState.APPROVED},
    BookingState.APPROVED: {BookingState.PAID},
}

_CANCEL_STATES = {BookingState.CANCELLED_BY_WORKER, BookingState.CANCELLED_BY_OPERATOR}
_CANCELLABLE_FROM = {BookingState.REQUESTED, BookingState.CONFIRMED}


def allowed_next_states(current: BookingState) -> set[BookingState]:
    next_states = set(_NEXT.get(current, set()))
    if current in _CANCELLABLE_FROM:
        next_states |= _CANCEL_STATES
    return next_states


def is_valid_transition(current: BookingState, target: BookingState) -> bool:
    return target in allowed_next_states(current)


def require_transition(current: BookingState, target: BookingState) -> None:
    if not is_valid_transition(current, target):
        raise TransitionError(f"Invalid transition: {current.value} -> {target.value}")

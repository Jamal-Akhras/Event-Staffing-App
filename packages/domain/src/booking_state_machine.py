from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Set

from packages.domain.src.booking_state import BookingState


@dataclass(frozen=True)
class Transition:
    from_state: BookingState
    to_state: BookingState


class TransitionError(ValueError):
    pass


_ALLOWED_TRANSITIONS: Set[Transition] = {
    Transition(BookingState.REQUESTED, BookingState.CONFIRMED),
    Transition(BookingState.CONFIRMED, BookingState.CHECKED_IN),
    Transition(BookingState.CHECKED_IN, BookingState.CHECKED_OUT),
    Transition(BookingState.CHECKED_OUT, BookingState.APPROVED),
    Transition(BookingState.APPROVED, BookingState.PAID),
    Transition(BookingState.CONFIRMED, BookingState.NO_SHOW),
}

_CANCEL_STATES: Set[BookingState] = {
    BookingState.CANCELLED_BY_WORKER,
    BookingState.CANCELLED_BY_OPERATOR,
}


def allowed_next_states(current: BookingState) -> Set[BookingState]:
    if current == BookingState.PAID:
        return set()

    next_states = {t.to_state for t in _ALLOWED_TRANSITIONS if t.from_state == current}
    next_states.update(_CANCEL_STATES)
    return next_states


def is_valid_transition(current: BookingState, target: BookingState) -> bool:
    if current == BookingState.PAID:
        return False
    if target in _CANCEL_STATES:
        return True
    return Transition(current, target) in _ALLOWED_TRANSITIONS


def require_transition(current: BookingState, target: BookingState) -> None:
    if not is_valid_transition(current, target):
        raise TransitionError(f"Invalid transition: {current.value} -> {target.value}")


def transition(current: BookingState, target: BookingState) -> BookingState:
    require_transition(current, target)
    return target

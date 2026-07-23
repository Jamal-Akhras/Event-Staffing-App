from __future__ import annotations

from uuid import uuid4

from apps.api.src.helpers import _now_or
from apps.api.src.repositories.booking_repository import BookingRepository
from apps.api.src.repositories.shift_repository import ShiftRepository
from apps.api.src.repositories.worker_profile_repository import WorkerProfileRepository
from apps.api.src.schemas import BookingCreateRequest, BookingTransitionRequest
from apps.api.src.services.booking_ops import _decrement_workers_filled, refresh_reliability, sweep_no_shows
from apps.api.src.services.errors import NotFoundError, ValidationError
from packages.domain.src.booking import Booking
from packages.domain.src.booking_state import BookingState
from packages.domain.src.booking_state_machine import TransitionError

_CANCELLATION_STATES = {
    BookingState.CANCELLED_BY_WORKER,
    BookingState.CANCELLED_BY_OPERATOR,
    BookingState.NO_SHOW,
}


class BookingLifecycleService:
    def __init__(
        self,
        booking_repo: BookingRepository,
        worker_repo: WorkerProfileRepository,
        shift_repo: ShiftRepository,
    ) -> None:
        self._bookings = booking_repo
        self._workers = worker_repo
        self._shifts = shift_repo

    def create_booking(self, request: BookingCreateRequest) -> Booking:
        return self._bookings.save(
            Booking(
                booking_id=str(uuid4()),
                shift_id=request.shift_id,
                worker_id=request.worker_id,
                operator_id=request.operator_id,
                start_time=request.start_time,
                end_time=request.end_time,
                created_at=_now_or(request.now),
            )
        )

    def get_booking(self, booking_id: str) -> Booking:
        booking = self._bookings.get(booking_id)
        if booking is None:
            raise NotFoundError("Booking not found.")
        return booking

    def list_bookings(
        self,
        limit: int = 25,
        worker_id: str | None = None,
        operator_id: str | None = None,
        account_id: str | None = None,
    ) -> list[Booking]:
        if account_id:
            return self._bookings.list_for_account(account_id, limit, worker_id)
        if worker_id:
            return self._bookings.list_by_worker(worker_id, limit, operator_id)
        if operator_id:
            return self._bookings.list_by_operator(operator_id, limit)
        return self._bookings.list_recent(limit)

    def transition(
        self,
        booking_id: str,
        target: BookingState,
        request: BookingTransitionRequest,
        refresh_worker_reliability: bool = False,
    ) -> Booking:
        now = _now_or(request.now)
        booking = self.get_booking(booking_id)
        try:
            booking = booking.transition_to(target, now)
        except TransitionError as exc:
            raise ValidationError(str(exc)) from exc
        booking = self._bookings.save(booking)
        if target in _CANCELLATION_STATES:
            _decrement_workers_filled(self._shifts, booking.shift_id)
        if refresh_worker_reliability:
            refresh_reliability(self._bookings, self._workers, booking.worker_id, now)
        return booking

    def sweep_no_shows(self, request: BookingTransitionRequest) -> list[Booking]:
        return sweep_no_shows(self._bookings, self._workers, self._shifts, _now_or(request.now))

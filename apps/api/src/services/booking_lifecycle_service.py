from __future__ import annotations

from dataclasses import replace

from apps.api.src.helpers import _now_or
from apps.api.src.repositories.booking_repository import BookingRepository
from apps.api.src.repositories.shift_repository import ShiftRepository
from apps.api.src.repositories.worker_profile_repository import WorkerProfileRepository
from apps.api.src.schemas import BookingTransitionRequest
from apps.api.src.schemas_recovery import CancellationRequest, PaymentRecordRequest
from apps.api.src.services.booking_ops import _decrement_workers_filled, refresh_reliability, sweep_no_shows
from apps.api.src.services.errors import NotFoundError, ValidationError
from apps.api.src.services.recovery_notifications import notify_worker
from apps.api.src.services.outbox_publisher import OutboxPublisher
from packages.domain.src.attendance import code_matches
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
        outbox: OutboxPublisher,
    ) -> None:
        self._bookings = booking_repo
        self._workers = worker_repo
        self._shifts = shift_repo
        self._outbox = outbox

    def get_booking(self, booking_id: str) -> Booking:
        booking = self._bookings.get(booking_id)
        if booking is None:
            raise NotFoundError("Booking not found.")
        return booking

    def booking_belongs_to_venue(self, booking: Booking, venue_id: str | None) -> bool:
        shift = self._shifts.get(booking.shift_id)
        return shift is not None and venue_id is not None and shift.account_id == venue_id

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
        request: BookingTransitionRequest | CancellationRequest | PaymentRecordRequest,
        actor_user_id: str,
        refresh_worker_reliability: bool = False,
    ) -> Booking:
        now = _now_or(request.now)
        booking = self.get_booking(booking_id)
        submitted = request.code if isinstance(request, BookingTransitionRequest) else None
        if target == BookingState.CHECKED_IN and not code_matches(submitted, booking.check_in_code):
            raise ValidationError("That check-in code doesn't match. Ask the manager for the code on their board.")
        if target == BookingState.APPROVED and not code_matches(submitted, booking.completion_code):
            raise ValidationError("That completion code doesn't match. Ask the worker to show the code in their app.")
        try:
            booking = booking.transition_to(target, now)
        except TransitionError as exc:
            raise ValidationError(str(exc)) from exc
        cancellation_reason = None
        if target in {BookingState.CANCELLED_BY_WORKER, BookingState.CANCELLED_BY_OPERATOR}:
            if not isinstance(request, CancellationRequest) or not request.reason:
                raise ValidationError("A cancellation reason and authenticated actor are required.")
            cancellation_reason = request.reason.strip()
            booking = replace(booking, cancellation_reason=cancellation_reason, cancelled_by_user_id=actor_user_id)
        if target == BookingState.PAID:
            if not isinstance(request, PaymentRecordRequest) or not request.method:
                raise ValidationError("Payment method and authenticated recorder are required.")
            booking = replace(
                booking,
                payment_method=request.method,
                payment_reference=request.reference,
                payment_recorded_by_user_id=actor_user_id,
            )
        booking = self._bookings.save(booking)
        if target in _CANCELLATION_STATES:
            _decrement_workers_filled(self._shifts, booking.shift_id, now)
        if target == BookingState.CANCELLED_BY_OPERATOR:
            notify_worker(
                self._outbox,
                booking.worker_id,
                booking.shift_id,
                "booking_cancelled",
                "Your booking was cancelled",
                cancellation_reason or "The venue cancelled this booking.",
            )
        if target == BookingState.CANCELLED_BY_WORKER:
            shift = self._shifts.get(booking.shift_id)
            if shift and shift.account_id:
                self._outbox.publish_notification(
                    event_type="booking.cancelled_by_worker",
                    aggregate_type="booking",
                    aggregate_id=booking.booking_id,
                    recipient_kind="venue",
                    recipient_id=shift.account_id,
                    category="shift_changes",
                    title="Worker cancelled booking",
                    body=cancellation_reason or "A worker cancelled their booking.",
                    action_kind="booking",
                    action_entity_id=booking.booking_id,
                )
        if refresh_worker_reliability:
            refresh_reliability(self._bookings, self._workers, booking.worker_id, now)
        return booking

    def sweep_no_shows(self, request: BookingTransitionRequest) -> list[Booking]:
        updated = sweep_no_shows(self._bookings, self._workers, self._shifts, _now_or(request.now))
        for booking in updated:
            shift = self._shifts.get(booking.shift_id)
            if shift and shift.account_id:
                self._outbox.publish_notification(
                    event_type="booking.no_show",
                    aggregate_type="booking",
                    aggregate_id=booking.booking_id,
                    recipient_kind="venue",
                    recipient_id=shift.account_id,
                    category="attendance",
                    title="Worker marked as no-show",
                    body="A booked worker missed their shift check-in window.",
                    action_kind="booking",
                    action_entity_id=booking.booking_id,
                )
        return updated

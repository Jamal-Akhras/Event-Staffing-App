from __future__ import annotations

from dataclasses import replace

from apps.api.src.datetime_utils import _now_or
from apps.api.src.models.shift import Shift
from apps.api.src.repositories.application_repository import ApplicationRepository
from apps.api.src.repositories.booking_repository import BookingRepository
from apps.api.src.repositories.shift_repository import ShiftRepository
from apps.api.src.schemas_recovery import CancellationRequest, ShiftLifecycleRequest, ShiftUpdateRequest
from apps.api.src.services.errors import NotFoundError, ValidationError
from apps.api.src.services.recovery_notifications import notify_worker
from apps.api.src.services.outbox_publisher import OutboxPublisher
from packages.domain.src.booking_state import BookingState
from packages.domain.src.booking_state_machine import TransitionError

_ACTIVE_BOOKING_STATES = {BookingState.REQUESTED, BookingState.CONFIRMED}
_IN_PROGRESS_BOOKING_STATES = {
    BookingState.CHECKED_IN,
    BookingState.CHECKED_OUT,
    BookingState.APPROVED,
    BookingState.PAID,
}


class ShiftLifecycleService:
    def __init__(
        self,
        shifts: ShiftRepository,
        applications: ApplicationRepository,
        bookings: BookingRepository,
        outbox: OutboxPublisher,
    ) -> None:
        self._shifts = shifts
        self._applications = applications
        self._bookings = bookings
        self._outbox = outbox

    def update(self, shift_id: str, request: ShiftUpdateRequest) -> Shift:
        shift = self._manageable_shift(shift_id, request.now)
        now = _now_or(request.now)
        bookings = self._bookings.list_by_shift(shift_id, for_update=True)
        active_bookings = [item for item in bookings if item.state in _ACTIVE_BOOKING_STATES]
        if request.workers_needed < shift.workers_filled:
            raise ValidationError("Workers needed cannot be below the number already booked.")
        if active_bookings and self._contract_terms_changed(shift, request):
            raise ValidationError(
                "Role, location, times and pay are locked once a worker is booked. "
                "Cancel the affected booking first or update only notes and capacity."
            )

        status = "filled" if shift.workers_filled >= request.workers_needed else "open"
        updated = self._shifts.save(
            replace(
                shift,
                role=request.role.strip(),
                location=request.location.strip(),
                start_time=request.start_time,
                end_time=request.end_time,
                pay_rate=request.pay_rate,
                notes=request.notes.strip() if request.notes else None,
                workers_needed=request.workers_needed,
                required_certification=request.required_certification,
                risk_information=request.risk_information,
                status=status,
                updated_at=now,
            )
        )
        for application in self._applications.list_by_shift(shift_id, for_update=True):
            if application.status == "applied":
                self._applications.save(
                    replace(application, start_time=updated.start_time, end_time=updated.end_time)
                )
        return updated

    def close(self, shift_id: str, request: ShiftLifecycleRequest) -> Shift:
        shift = self._manageable_shift(shift_id, request.now)
        now = _now_or(request.now)
        self._reject_pending_applications(shift, now, "Shift closed", "This shift is no longer accepting applications.")
        return self._shifts.save(replace(shift, status="closed", closed_at=now, updated_at=now))

    def cancel(
        self,
        shift_id: str,
        request: CancellationRequest,
        cancelled_by_user_id: str,
    ) -> Shift:
        shift = self._manageable_shift(shift_id, request.now, allow_closed=True)
        now = _now_or(request.now)
        bookings = self._bookings.list_by_shift(shift_id, for_update=True)
        if any(item.state in _IN_PROGRESS_BOOKING_STATES for item in bookings):
            raise ValidationError("This shift has already started for at least one worker and cannot be cancelled.")

        for booking in bookings:
            if booking.state not in _ACTIVE_BOOKING_STATES:
                continue
            try:
                cancelled = booking.transition_to(BookingState.CANCELLED_BY_OPERATOR, now)
            except TransitionError as exc:
                raise ValidationError(str(exc)) from exc
            self._bookings.save(
                replace(
                    cancelled,
                    cancellation_reason=request.reason.strip(),
                    cancelled_by_user_id=cancelled_by_user_id,
                )
            )
            notify_worker(
                self._outbox,
                booking.worker_id,
                shift_id,
                "shift_cancelled",
                "Shift cancelled by venue",
                request.reason.strip(),
            )

        self._reject_pending_applications(
            shift,
            now,
            "Shift cancelled",
            request.reason.strip(),
        )
        return self._shifts.save(
            replace(
                shift,
                status="cancelled",
                workers_filled=0,
                cancelled_at=now,
                cancellation_reason=request.reason.strip(),
                cancelled_by_user_id=cancelled_by_user_id,
                updated_at=now,
            )
        )

    def _manageable_shift(
        self,
        shift_id: str,
        requested_now,
        allow_closed: bool = False,
    ) -> Shift:
        shift = self._shifts.get_for_update(shift_id)
        if shift is None:
            raise NotFoundError("Shift not found.")
        allowed = {"open", "filled"}
        if allow_closed:
            allowed.add("closed")
        if shift.status not in allowed:
            raise ValidationError(f"A {shift.status} shift can no longer be changed.")
        if _now_or(requested_now) >= shift.start_time:
            raise ValidationError("This shift has already started and can no longer be changed.")
        return shift

    def _reject_pending_applications(self, shift: Shift, now, title: str, body: str) -> None:
        for application in self._applications.list_by_shift(shift.shift_id, for_update=True):
            if application.status != "applied":
                continue
            self._applications.save(replace(application, status="rejected", decided_at=now))
            notify_worker(
                self._outbox,
                application.worker_id,
                shift.shift_id,
                "shift_unavailable",
                title,
                body,
            )

    @staticmethod
    def _contract_terms_changed(shift: Shift, request: ShiftUpdateRequest) -> bool:
        return any(
            (
                request.role.strip() != shift.role,
                request.location.strip() != shift.location,
                request.start_time != shift.start_time,
                request.end_time != shift.end_time,
                request.pay_rate != shift.pay_rate,
            )
        )

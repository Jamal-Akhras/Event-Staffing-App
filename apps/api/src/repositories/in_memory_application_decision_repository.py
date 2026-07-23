from __future__ import annotations

from dataclasses import replace
from datetime import datetime
from threading import Lock

from apps.api.src.models.application import Application
from apps.api.src.repositories.application_decision_repository import (
    ApplicationAlreadyDecidedError,
    ApplicationApprovalResult,
    ApplicationDecisionNotFoundError,
    ShiftAlreadyFullError,
)
from apps.api.src.repositories.application_repository import ApplicationRepository
from apps.api.src.repositories.booking_repository import BookingRepository
from apps.api.src.repositories.shift_repository import ShiftRepository
from packages.domain.src.booking import Booking
from packages.domain.src.booking_state import BookingState


class InMemoryApplicationDecisionRepository:
    def __init__(
        self,
        applications: ApplicationRepository,
        bookings: BookingRepository,
        shifts: ShiftRepository,
    ) -> None:
        self._applications = applications
        self._bookings = bookings
        self._shifts = shifts
        self._lock = Lock()

    def approve(
        self,
        application_id: str,
        now: datetime,
        booking_id: str,
    ) -> ApplicationApprovalResult:
        with self._lock:
            application = self._get_applied_application(application_id)
            shift = self._shifts.get(application.shift_id)
            if shift is None:
                raise ApplicationDecisionNotFoundError("Shift not found.")
            if shift.workers_filled >= shift.workers_needed:
                raise ShiftAlreadyFullError("Shift is already fully staffed.")

            booking = Booking(
                booking_id=booking_id,
                shift_id=application.shift_id,
                worker_id=application.worker_id,
                operator_id=application.operator_id,
                start_time=application.start_time,
                end_time=application.end_time,
                created_at=now,
            ).transition_to(BookingState.CONFIRMED, now)
            self._bookings.save(booking)

            workers_filled = shift.workers_filled + 1
            status = "filled" if workers_filled >= shift.workers_needed else shift.status
            shift = replace(shift, workers_filled=workers_filled, status=status)
            self._shifts.save(shift)

            application = replace(
                application,
                status="approved",
                decided_at=now,
                booking_id=booking.booking_id,
            )
            application = self._applications.save(application)
            return ApplicationApprovalResult(application=application, booking=booking, shift=shift)

    def reject(self, application_id: str, now: datetime) -> Application:
        with self._lock:
            application = self._get_applied_application(application_id)
            return self._applications.save(
                replace(application, status="rejected", decided_at=now),
            )

    def _get_applied_application(self, application_id: str) -> Application:
        application = self._applications.get(application_id)
        if application is None:
            raise ApplicationDecisionNotFoundError("Application not found.")
        if application.status != "applied":
            raise ApplicationAlreadyDecidedError("Application already decided.")
        return application

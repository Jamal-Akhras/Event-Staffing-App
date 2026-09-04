from __future__ import annotations

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from apps.api.src.db.models import ApplicationModel, BookingModel, ShiftModel
from apps.api.src.money import money
from apps.api.src.models.application import Application
from apps.api.src.models.shift import Shift
from apps.api.src.repositories.booking_allocator import (
    AllocationTargetMissingError,
    ShiftFullError,
    WorkerAlreadyBookedError,
)
from apps.api.src.repositories.application_decision_repository import (
    ApplicationAlreadyDecidedError,
    ApplicationApprovalResult,
    ApplicationDecisionConflictError,
    ApplicationDecisionNotFoundError,
    ShiftAlreadyFullError,
)
from packages.domain.src.booking import Booking
from packages.domain.src.booking_state import BookingState


class SqlAlchemyApplicationDecisionRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def approve(
        self,
        application_id: str,
        now: datetime,
        booking_id: str,
        attendance_mode: str = "pin",
    ) -> ApplicationApprovalResult:
        from apps.api.src.repositories.sqlalchemy_booking_allocator import SqlAlchemyBookingAllocator

        try:
            with self._session.begin_nested():
                application_model = self._load_application_for_update(application_id)
                if application_model.status != "applied":
                    raise ApplicationAlreadyDecidedError("Application already decided.")

                allocated = SqlAlchemyBookingAllocator(self._session).allocate(
                    application_model.shift_id,
                    application_model.worker_id,
                    now,
                    booking_id,
                    attendance_mode=attendance_mode,
                )

                application_model.status = "approved"
                application_model.decided_at = now
                application_model.booking_id = booking_id
                self._session.flush()
        except AllocationTargetMissingError as exc:
            raise ApplicationDecisionNotFoundError("Shift not found.") from exc
        except ShiftFullError as exc:
            raise ShiftAlreadyFullError("Shift is already fully staffed.") from exc
        except WorkerAlreadyBookedError as exc:
            raise ApplicationDecisionConflictError("Application decision could not be saved.") from exc
        except IntegrityError as exc:
            raise ApplicationDecisionConflictError("Application decision could not be saved.") from exc

        return ApplicationApprovalResult(
            application=_application_to_domain(application_model),
            booking=allocated.booking,
            shift=allocated.shift,
        )

    def reject(self, application_id: str, now: datetime) -> Application:
        application_model = self._load_application_for_update(application_id)
        if application_model.status != "applied":
            raise ApplicationAlreadyDecidedError("Application already decided.")
        application_model.status = "rejected"
        application_model.decided_at = now
        self._session.flush()
        return _application_to_domain(application_model)

    def _load_application_for_update(self, application_id: str) -> ApplicationModel:
        application_model = self._session.execute(
            select(ApplicationModel)
            .where(ApplicationModel.application_id == application_id)
            .with_for_update()
        ).scalar_one_or_none()
        if application_model is None:
            raise ApplicationDecisionNotFoundError("Application not found.")
        return application_model

    def _load_shift_for_update(self, shift_id: str) -> ShiftModel:
        shift_model = self._session.execute(
            select(ShiftModel)
            .where(ShiftModel.shift_id == shift_id)
            .with_for_update()
        ).scalar_one_or_none()
        if shift_model is None:
            raise ApplicationDecisionNotFoundError("Shift not found.")
        return shift_model


def _booking_to_model(booking: Booking) -> BookingModel:
    return BookingModel(
        booking_id=booking.booking_id,
        shift_id=booking.shift_id,
        worker_id=booking.worker_id,
        operator_id=booking.operator_id,
        start_time=booking.start_time,
        end_time=booking.end_time,
        state=booking.state,
        created_at=booking.created_at,
        confirmed_at=booking.confirmed_at,
        checked_in_at=booking.checked_in_at,
        checked_out_at=booking.checked_out_at,
        approved_at=booking.approved_at,
        paid_at=booking.paid_at,
        cancelled_at=booking.cancelled_at,
        no_show_at=booking.no_show_at,
        check_in_code=booking.check_in_code,
        completion_code=booking.completion_code,
        attendance_mode=booking.attendance_mode,
        allocation_source=booking.allocation_source,
        override_checked_in_at=booking.override_checked_in_at,
        override_checked_out_at=booking.override_checked_out_at,
    )


def _booking_to_domain(model: BookingModel) -> Booking:
    return Booking(
        booking_id=model.booking_id,
        shift_id=model.shift_id,
        worker_id=model.worker_id,
        operator_id=model.operator_id,
        start_time=model.start_time,
        end_time=model.end_time,
        state=model.state,
        created_at=model.created_at,
        confirmed_at=model.confirmed_at,
        checked_in_at=model.checked_in_at,
        checked_out_at=model.checked_out_at,
        approved_at=model.approved_at,
        paid_at=model.paid_at,
        cancelled_at=model.cancelled_at,
        no_show_at=model.no_show_at,
        check_in_code=model.check_in_code,
        completion_code=model.completion_code,
        attendance_mode=model.attendance_mode,
        allocation_source=model.allocation_source,
        override_checked_in_at=model.override_checked_in_at,
        override_checked_out_at=model.override_checked_out_at,
    )


def _application_to_domain(model: ApplicationModel) -> Application:
    return Application(
        application_id=model.application_id,
        shift_id=model.shift_id,
        worker_id=model.worker_id,
        operator_id=model.operator_id,
        start_time=model.start_time,
        end_time=model.end_time,
        message=model.message,
        booking_id=model.booking_id,
        status=model.status,
        created_at=model.created_at,
        decided_at=model.decided_at,
    )


def _shift_to_domain(model: ShiftModel) -> Shift:
    return Shift(
        shift_id=model.shift_id,
        operator_id=model.operator_id,
        role=model.role,
        location=model.location,
        start_time=model.start_time,
        end_time=model.end_time,
        pay_rate=money(model.pay_rate),
        notes=model.notes,
        status=model.status,
        created_at=model.created_at,
        workers_needed=model.workers_needed,
        workers_filled=model.workers_filled,
    )

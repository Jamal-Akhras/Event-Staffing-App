from __future__ import annotations

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from apps.api.src.db.models import ApplicationModel, BookingModel, ShiftModel
from apps.api.src.models.application import Application
from apps.api.src.models.shift import Shift
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
    ) -> ApplicationApprovalResult:
        try:
            with self._session.begin():
                application_model = self._load_application_for_update(application_id)
                if application_model.status != "applied":
                    raise ApplicationAlreadyDecidedError("Application already decided.")

                shift_model = self._load_shift_for_update(application_model.shift_id)
                if shift_model.workers_filled >= shift_model.workers_needed:
                    raise ShiftAlreadyFullError("Shift is already fully staffed.")

                booking = Booking(
                    booking_id=booking_id,
                    shift_id=application_model.shift_id,
                    worker_id=application_model.worker_id,
                    operator_id=application_model.operator_id,
                    start_time=application_model.start_time,
                    end_time=application_model.end_time,
                    created_at=now,
                ).transition_to(BookingState.CONFIRMED, now)
                booking_model = _booking_to_model(booking)
                self._session.add(booking_model)

                workers_filled = shift_model.workers_filled + 1
                shift_model.workers_filled = workers_filled
                if workers_filled >= shift_model.workers_needed:
                    shift_model.status = "filled"

                application_model.status = "approved"
                application_model.decided_at = now
                application_model.booking_id = booking.booking_id
        except IntegrityError as exc:
            self._session.rollback()
            raise ApplicationDecisionConflictError("Application decision could not be saved.") from exc

        return ApplicationApprovalResult(
            application=_application_to_domain(application_model),
            booking=_booking_to_domain(booking_model),
            shift=_shift_to_domain(shift_model),
        )

    def reject(self, application_id: str, now: datetime) -> Application:
        with self._session.begin():
            application_model = self._load_application_for_update(application_id)
            if application_model.status != "applied":
                raise ApplicationAlreadyDecidedError("Application already decided.")
            application_model.status = "rejected"
            application_model.decided_at = now
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
        pay_rate=model.pay_rate,
        notes=model.notes,
        status=model.status,
        created_at=model.created_at,
        workers_needed=model.workers_needed,
        workers_filled=model.workers_filled,
    )

from __future__ import annotations

from dataclasses import replace
from uuid import uuid4

from apps.api.src.helpers import _now_or
from apps.api.src.models.application import Application
from apps.api.src.models.application_message_history import ApplicationMessageHistory
from apps.api.src.repositories.application_decision_repository import (
    ApplicationAlreadyDecidedError,
    ApplicationDecisionConflictError,
    ApplicationDecisionNotFoundError,
    ApplicationDecisionRepository,
    ShiftAlreadyFullError,
)
from apps.api.src.repositories.application_message_history_repository import (
    ApplicationMessageHistoryRepository,
)
from apps.api.src.repositories.application_repository import (
    ApplicationRepository,
    DuplicateApplicationError,
)
from apps.api.src.repositories.shift_repository import ShiftRepository
from apps.api.src.schemas import (
    ApplicationCreateRequest,
    ApplicationDecisionRequest,
    ApplicationMessageUpdateRequest,
)
from apps.api.src.schemas_recovery import CancellationRequest
from apps.api.src.models.worker_relationship import EMPLOYED_TYPES
from apps.api.src.repositories.booking_allocator import OverlappingBookingError
from apps.api.src.repositories.worker_relationship_repository import WorkerRelationshipRepository
from apps.api.src.services.errors import ConflictError, ForbiddenError, NotFoundError, ValidationError
from apps.api.src.services.shift_visibility import worker_can_see_shift
from apps.api.src.services.outbox_publisher import OutboxPublisher


class ApplicationService:
    def __init__(
        self,
        application_repo: ApplicationRepository,
        shift_repo: ShiftRepository,
        decision_repo: ApplicationDecisionRepository,
        history_repo: ApplicationMessageHistoryRepository,
        outbox: OutboxPublisher,
        relationships: WorkerRelationshipRepository,
    ) -> None:
        self._applications = application_repo
        self._shifts = shift_repo
        self._decisions = decision_repo
        self._history = history_repo
        self._outbox = outbox
        self._relationships = relationships

    def create_application(self, request: ApplicationCreateRequest) -> Application:
        shift = self._shifts.get(request.shift_id)
        if shift is None:
            raise NotFoundError("Shift not found.")
        if shift.status != "open":
            raise ValidationError("Shift is not accepting applications.")
        if shift.workers_filled >= shift.workers_needed:
            raise ValidationError("Shift is already fully staffed.")
        if not worker_can_see_shift(shift, request.worker_id, self._relationships):
            raise ForbiddenError("This shift is not open to you.")
        if self._applications.find_by_worker_and_shift(request.worker_id, request.shift_id):
            raise ValidationError("You have already applied to this shift. You can only apply once per shift.")

        application = Application(
            application_id=str(uuid4()),
            shift_id=shift.shift_id,
            worker_id=request.worker_id,
            operator_id=shift.operator_id,
            start_time=shift.start_time,
            end_time=shift.end_time,
            message=request.message,
            booking_id=None,
            status="applied",
            created_at=_now_or(request.now),
        )
        try:
            saved = self._applications.save(application)
            if shift.account_id:
                self._outbox.publish_notification(
                    event_type="application.created",
                    aggregate_type="application",
                    aggregate_id=saved.application_id,
                    recipient_kind="venue",
                    recipient_id=shift.account_id,
                    category="applications",
                    title="New shift application",
                    body="A worker applied to your shift.",
                    action_kind="application",
                    action_entity_id=saved.application_id,
                )
            return saved
        except DuplicateApplicationError as exc:
            raise ValidationError("You have already applied to this shift. You can only apply once per shift.") from exc

    def list_applications(
        self,
        limit: int = 50,
        status: str | None = None,
        worker_id: str | None = None,
        operator_id: str | None = None,
        account_id: str | None = None,
        shift_id: str | None = None,
    ) -> list[Application]:
        if account_id:
            return self._applications.list_for_account(account_id, limit, status, shift_id, worker_id)
        if worker_id:
            return self._applications.list_by_worker(worker_id, limit, status, shift_id, operator_id)
        if operator_id:
            return self._applications.list_by_operator(operator_id, limit, status, shift_id)
        return self._applications.list_recent(limit, status, shift_id)

    def _attendance_mode_for(self, application_id: str) -> str:
        application = self._applications.get(application_id)
        if application is None:
            return "pin"
        shift = self._shifts.get(application.shift_id)
        if shift is None or not shift.account_id:
            return "pin"
        relationship = self._relationships.get_for_venue_worker(shift.account_id, application.worker_id)
        if (
            relationship is not None
            and relationship.status == "active"
            and relationship.relationship_type in EMPLOYED_TYPES
        ):
            return "employed"
        return "pin"

    def approve_application(self, application_id: str, request: ApplicationDecisionRequest) -> Application:
        try:
            result = self._decisions.approve(
                application_id,
                _now_or(request.now),
                str(uuid4()),
                attendance_mode=self._attendance_mode_for(application_id),
            )
        except ApplicationDecisionNotFoundError as exc:
            raise NotFoundError(str(exc)) from exc
        except (ApplicationAlreadyDecidedError, ShiftAlreadyFullError) as exc:
            raise ValidationError(str(exc)) from exc
        except OverlappingBookingError as exc:
            raise ValidationError("Worker is already booked on an overlapping shift.") from exc
        except ApplicationDecisionConflictError as exc:
            raise ConflictError(str(exc)) from exc
        self._publish_decision(result.application, "approved")
        return result.application

    def reject_application(self, application_id: str, request: ApplicationDecisionRequest) -> Application:
        try:
            application = self._decisions.reject(application_id, _now_or(request.now))
            self._publish_decision(application, "rejected")
            return application
        except ApplicationDecisionNotFoundError as exc:
            raise NotFoundError(str(exc)) from exc
        except ApplicationAlreadyDecidedError as exc:
            raise ValidationError(str(exc)) from exc

    def update_message(self, application_id: str, request: ApplicationMessageUpdateRequest) -> Application:
        application = self._get_application(application_id)
        if application.status != "applied":
            raise ValidationError("Can only edit message for pending applications.")

        now = _now_or(request.now)
        if application.message:
            self._history.save(
                ApplicationMessageHistory(
                    history_id=str(uuid4()),
                    application_id=application_id,
                    message=application.message,
                    edited_at=now,
                )
            )

        return self._applications.save(replace(application, message=request.message))

    def withdraw(self, application_id: str, request: CancellationRequest) -> Application:
        application = self._get_application(application_id)
        if application.status != "applied":
            raise ValidationError("Only pending applications can be withdrawn.")
        now = _now_or(request.now)
        if now >= application.start_time:
            raise ValidationError("This shift has already started.")
        withdrawn = self._applications.save(
            replace(
                application,
                status="withdrawn",
                decided_at=now,
                withdrawn_at=now,
                withdrawal_reason=request.reason.strip(),
            )
        )
        shift = self._shifts.get(withdrawn.shift_id)
        if shift and shift.account_id:
            self._outbox.publish_notification(
                event_type="application.withdrawn",
                aggregate_type="application",
                aggregate_id=withdrawn.application_id,
                recipient_kind="venue",
                recipient_id=shift.account_id,
                category="applications",
                title="Application withdrawn",
                body="A worker withdrew their shift application.",
                action_kind="application",
                action_entity_id=withdrawn.application_id,
            )
        return withdrawn

    def list_message_history(self, application_id: str) -> list[ApplicationMessageHistory]:
        self._get_application(application_id)
        return self._history.list_by_application(application_id)

    def get_application(self, application_id: str) -> Application:
        return self._get_application(application_id)

    def application_belongs_to_venue(self, application: Application, venue_id: str | None) -> bool:
        shift = self._shifts.get(application.shift_id)
        return shift is not None and venue_id is not None and shift.account_id == venue_id

    def _get_application(self, application_id: str) -> Application:
        application = self._applications.get(application_id)
        if application is None:
            raise NotFoundError("Application not found.")
        return application

    def _publish_decision(self, application: Application, decision: str) -> None:
        date_str = application.start_time.strftime("%a %d %b")
        title = "Application approved" if decision == "approved" else "Application not selected"
        self._outbox.publish_notification(
            event_type=f"application.{decision}",
            aggregate_type="application",
            aggregate_id=application.application_id,
            recipient_kind="worker",
            recipient_id=application.worker_id,
            category="applications",
            title=title,
            body=f"Your application for {date_str} has been {decision}.",
            action_kind="application",
            action_entity_id=application.application_id,
        )

from __future__ import annotations

from dataclasses import replace
from datetime import datetime
from uuid import uuid4

from apps.api.src.models.booking_transition import BookingTransition
from apps.api.src.models.shift_change_request import ShiftChangeRequest, ShiftChangeTransition
from apps.api.src.models.worker_relationship import EMPLOYED_TYPES
from apps.api.src.repositories.booking_allocator import (
    BookingAllocator,
    OverlappingBookingError,
    ShiftFullError,
    WorkerAlreadyBookedError,
)
from apps.api.src.repositories.booking_repository import BookingRepository
from apps.api.src.repositories.booking_transition_repository import BookingTransitionRepository
from apps.api.src.repositories.shift_change_request_repository import (
    DuplicatePendingChangeError,
    ShiftChangeRequestRepository,
    ShiftChangeTransitionRepository,
)
from apps.api.src.repositories.shift_repository import ShiftRepository
from apps.api.src.repositories.worker_relationship_repository import WorkerRelationshipRepository
from apps.api.src.schemas_recovery import CancellationRequest
from apps.api.src.services.booking_lifecycle_service import BookingLifecycleService
from apps.api.src.services.errors import ConflictError, NotFoundError, ValidationError
from apps.api.src.services.outbox_publisher import OutboxPublisher
from apps.api.src.services.rota_revisions import RotaRevisionService
from packages.domain.src.booking import Booking
from packages.domain.src.booking_state import BookingState


class ShiftChangeService:
    def __init__(
        self,
        requests: ShiftChangeRequestRepository,
        change_transitions: ShiftChangeTransitionRepository,
        shifts: ShiftRepository,
        bookings: BookingRepository,
        allocator: BookingAllocator,
        relationships: WorkerRelationshipRepository,
        booking_transitions: BookingTransitionRepository,
        lifecycle: BookingLifecycleService,
        escalations,
        outbox: OutboxPublisher,
        revisions: RotaRevisionService,
    ) -> None:
        self._requests = requests
        self._change_transitions = change_transitions
        self._shifts = shifts
        self._bookings = bookings
        self._allocator = allocator
        self._relationships = relationships
        self._booking_transitions = booking_transitions
        self._lifecycle = lifecycle
        self._escalations = escalations
        self._outbox = outbox
        self._revisions = revisions

    def list_requests_for_worker(self, worker_id: str):
        return self._requests.list_for_worker(worker_id)

    def list_requests_for_venue(self, venue_id: str, status: str | None = None):
        return self._requests.list_for_venue(venue_id, status)

    def request_release(
        self, worker_id: str, booking_id: str, reason: str, now: datetime
    ) -> ShiftChangeRequest:
        booking, shift = self._live_booking(worker_id, booking_id, now)
        request = self._create(
            booking, shift, worker_id, "release", None, reason, "pending_manager", now
        )
        self._notify_venue(
            request, "change_request.created", "A worker asked to be released",
            f"{shift.role} on {shift.start_time:%d %b}: {reason}",
        )
        return request

    def request_cover(
        self, worker_id: str, booking_id: str, replacement_worker_id: str, reason: str,
        now: datetime,
    ) -> ShiftChangeRequest:
        if replacement_worker_id == worker_id:
            raise ValidationError("Pick someone else to cover the shift.")
        booking, shift = self._live_booking(worker_id, booking_id, now)
        relationship = self._relationships.get_for_venue_worker(
            shift.account_id, replacement_worker_id
        )
        if (
            relationship is None
            or relationship.status != "active"
            or relationship.relationship_type == "one_off"
        ):
            raise ValidationError(
                "Cover has to come from the venue's team or pool: release the shift instead."
            )
        request = self._create(
            booking, shift, worker_id, "cover", replacement_worker_id, reason,
            "pending_replacement", now,
        )
        self._notify_worker(
            replacement_worker_id, request, "change_request.cover_asked",
            "A colleague asked you to cover",
            f"{shift.role} on {shift.start_time:%d %b}. Accept in the app to send it for approval.",
        )
        return request

    def accept_replacement(self, request_id: str, worker_id: str, now: datetime) -> ShiftChangeRequest:
        request = self._replacement_request(request_id, worker_id)
        moved = self._transition(request, "pending_manager", now, worker_id, "worker", None)
        self._notify_venue(
            moved, "change_request.ready", "A cover swap needs your approval",
            "The replacement accepted: approve or decline the change.",
        )
        return moved

    def decline_replacement(self, request_id: str, worker_id: str, now: datetime) -> ShiftChangeRequest:
        request = self._replacement_request(request_id, worker_id)
        declined = self._requests.save(
            replace(request, status="declined", decided_at=now, decided_by_user_id=worker_id,
                    updated_at=now)
        )
        self._append_change(request, "declined", now, worker_id, "worker", "Replacement declined.")
        self._notify_worker(
            request.worker_id, declined, "change_request.declined",
            "Your cover fell through",
            "They can't take it: pick someone else or ask to be released.",
        )
        return declined

    def withdraw(self, request_id: str, worker_id: str, now: datetime) -> ShiftChangeRequest:
        request = self._requests.get(request_id)
        if request is None or request.worker_id != worker_id:
            raise NotFoundError("That request was not found.")
        if request.status not in ("pending_replacement", "pending_manager"):
            raise ValidationError("This request has already been settled.")
        return self._transition(request, "withdrawn", now, worker_id, "worker", None)

    def approve(
        self, request_id: str, venue_id: str, actor_user_id: str, now: datetime
    ) -> ShiftChangeRequest:
        request = self._manager_request(request_id, venue_id)
        booking = self._bookings.get(request.booking_id)
        if booking is None or booking.state != BookingState.CONFIRMED:
            raise ValidationError("This booking has moved on: the request can no longer be approved.")
        if now >= booking.start_time:
            raise ValidationError("This shift has already started.")
        if request.change_type == "cover":
            self._approve_cover(request, booking, actor_user_id, now)
        else:
            self._approve_release(request, booking, actor_user_id, now)
        approved = self._requests.save(
            replace(request, status="approved", decided_at=now, decided_by_user_id=actor_user_id,
                    updated_at=now)
        )
        self._append_change(request, "approved", now, actor_user_id, "operator", None)
        self._notify_worker(
            request.worker_id, approved, "change_request.approved", "You're off the shift",
            "The venue approved your request.",
        )
        return approved

    def decline(
        self, request_id: str, venue_id: str, actor_user_id: str, now: datetime
    ) -> ShiftChangeRequest:
        request = self._manager_request(request_id, venue_id)
        declined = self._requests.save(
            replace(request, status="declined", decided_at=now, decided_by_user_id=actor_user_id,
                    updated_at=now)
        )
        self._append_change(request, "declined", now, actor_user_id, "operator", None)
        self._notify_worker(
            request.worker_id, declined, "change_request.declined", "Your request was declined",
            "The venue still needs you on this shift.",
        )
        return declined

    def expire_due(self, now: datetime) -> int:
        return expire_change_requests(
            self._requests, self._change_transitions, self._bookings, now
        )

    def _approve_release(
        self, request: ShiftChangeRequest, booking: Booking, actor_user_id: str, now: datetime
    ) -> None:
        with self._draft_guard(request.shift_id, now):
            self._cancel_booking(booking, request, "release_approved", actor_user_id, now)
        self._escalations.restart_ladder(request.shift_id, now)
        outcome = self._revisions.mint(
            request.venue_id, self._revisions.week_of(self._shifts.get(request.shift_id)),
            actor_user_id, now,
        )
        self._revisions.notify(outcome, exclude={request.worker_id})

    def _approve_cover(
        self, request: ShiftChangeRequest, booking: Booking, actor_user_id: str, now: datetime
    ) -> None:
        replacement = request.replacement_worker_id
        relationship = self._relationships.get_for_venue_worker(request.venue_id, replacement)
        if relationship is None or relationship.status != "active":
            raise ValidationError("The replacement no longer has an active relationship here.")
        try:
            self._allocator.check_availability(
                replacement, booking.start_time, booking.end_time, request.shift_id
            )
        except OverlappingBookingError as exc:
            raise ValidationError(
                f"The replacement now has an overlapping booking on shift {exc.clashing_shift_id}."
            ) from exc
        attendance_mode = (
            "employed" if relationship.relationship_type in EMPLOYED_TYPES else "pin"
        )
        with self._draft_guard(request.shift_id, now):
            self._cancel_booking(booking, request, "cover_approved", actor_user_id, now)
            try:
                allocated = self._allocator.allocate(
                    request.shift_id, replacement, now, str(uuid4()),
                    attendance_mode=attendance_mode,
                )
            except (ShiftFullError, WorkerAlreadyBookedError, OverlappingBookingError) as exc:
                raise ConflictError(
                    "The replacement could not be booked: reload and try again."
                ) from exc
            self._booking_transitions.append(
                BookingTransition(
                    transition_id=str(uuid4()),
                    booking_id=allocated.booking.booking_id,
                    from_state=None,
                    to_state="confirmed",
                    occurred_at=now,
                    actor_user_id=actor_user_id,
                    actor_role="operator",
                    reason_code="cover_approved",
                    context={"request_id": request.request_id, "shift_id": request.shift_id},
                )
            )
        outcome = self._revisions.mint(
            request.venue_id, self._revisions.week_of(self._shifts.get(request.shift_id)),
            actor_user_id, now,
        )
        self._revisions.notify(outcome, exclude={request.worker_id, replacement})
        self._notify_worker(
            replacement, request, "change_request.booked", "You're covering a shift",
            "The venue approved the cover: it's now in your shifts.",
        )

    def _draft_guard(self, shift_id: str, now: datetime):
        service = self

        class _Guard:
            def __enter__(self_inner):
                shift = service._shifts.get(shift_id)
                self_inner.was_published = shift is not None and shift.rota_state == "published"
                if self_inner.was_published:
                    service._shifts.save(replace(shift, rota_state="draft", updated_at=now))
                return self_inner

            def __exit__(self_inner, exc_type, exc, tb):
                shift = service._shifts.get(shift_id)
                if self_inner.was_published and shift is not None:
                    service._shifts.save(replace(shift, rota_state="published", updated_at=now))
                return False

        return _Guard()

    def _cancel_booking(
        self, booking: Booking, request: ShiftChangeRequest, reason_code: str,
        actor_user_id: str, now: datetime,
    ) -> None:
        self._lifecycle.transition(
            booking.booking_id,
            BookingState.CANCELLED_BY_OPERATOR,
            CancellationRequest(
                reason=f"Approved change request: {request.reason}", now=now,
                reason_code=reason_code,
            ),
            actor_user_id,
            actor_role="operator",
        )

    def _create(
        self, booking: Booking, shift, worker_id: str, change_type: str,
        replacement_worker_id: str | None, reason: str, status: str, now: datetime,
    ) -> ShiftChangeRequest:
        try:
            request = self._requests.save(
                ShiftChangeRequest(
                    request_id=str(uuid4()),
                    booking_id=booking.booking_id,
                    shift_id=booking.shift_id,
                    venue_id=shift.account_id,
                    worker_id=worker_id,
                    change_type=change_type,
                    status=status,
                    reason=reason,
                    replacement_worker_id=replacement_worker_id,
                    created_at=now,
                    updated_at=now,
                )
            )
        except DuplicatePendingChangeError as exc:
            raise ConflictError("This booking already has an open request.") from exc
        self._append_change(request, status, now, worker_id, "worker", None, from_status=None)
        return request

    def _transition(
        self, request: ShiftChangeRequest, to_status: str, now: datetime,
        actor_user_id: str | None, actor_role: str, note: str | None,
    ) -> ShiftChangeRequest:
        moved = self._requests.save(replace(request, status=to_status, updated_at=now))
        self._append_change(request, to_status, now, actor_user_id, actor_role, note)
        return moved

    def _append_change(
        self, request: ShiftChangeRequest, to_status: str, now: datetime,
        actor_user_id: str | None, actor_role: str, note: str | None,
        from_status: str | None = "",
    ) -> None:
        self._change_transitions.append(
            ShiftChangeTransition(
                transition_id=str(uuid4()),
                request_id=request.request_id,
                from_status=request.status if from_status == "" else from_status,
                to_status=to_status,
                occurred_at=now,
                actor_user_id=actor_user_id,
                actor_role=actor_role,
                note=note,
            )
        )

    def _live_booking(self, worker_id: str, booking_id: str, now: datetime):
        booking = self._bookings.get(booking_id)
        if booking is None or booking.worker_id != worker_id:
            raise NotFoundError("That booking was not found.")
        if booking.state != BookingState.CONFIRMED:
            raise ValidationError("Only a confirmed booking can be changed.")
        if now >= booking.start_time:
            raise ValidationError("This shift has already started.")
        shift = self._shifts.get(booking.shift_id)
        if shift is None or not shift.account_id:
            raise NotFoundError("That shift was not found.")
        return booking, shift

    def _replacement_request(self, request_id: str, worker_id: str) -> ShiftChangeRequest:
        request = self._requests.get(request_id)
        if request is None or request.replacement_worker_id != worker_id:
            raise NotFoundError("That request was not found.")
        if request.status != "pending_replacement":
            raise ValidationError("This request has already moved on.")
        return request

    def _manager_request(self, request_id: str, venue_id: str) -> ShiftChangeRequest:
        request = self._requests.get(request_id)
        if request is None or request.venue_id != venue_id:
            raise NotFoundError("That request was not found.")
        if request.status != "pending_manager":
            raise ValidationError("This request is not waiting on you.")
        return request

    def _notify_venue(
        self, request: ShiftChangeRequest, event_type: str, title: str, body: str
    ) -> None:
        self._outbox.publish_notification(
            event_type=event_type,
            aggregate_type="shift_change_request",
            aggregate_id=request.request_id,
            recipient_kind="venue",
            recipient_id=request.venue_id,
            category="shift_changes",
            title=title,
            body=body,
            action_kind="shift",
            action_entity_id=request.shift_id,
        )

    def _notify_worker(
        self, worker_id: str, request: ShiftChangeRequest, event_type: str, title: str, body: str
    ) -> None:
        self._outbox.publish_notification(
            event_type=event_type,
            aggregate_type="shift_change_request",
            aggregate_id=f"{request.request_id}:{worker_id}",
            recipient_kind="worker",
            recipient_id=worker_id,
            category="shift_changes",
            title=title,
            body=body,
            action_kind="shift",
            action_entity_id=request.shift_id,
        )


def expire_change_requests(requests, change_transitions, bookings, now: datetime) -> int:
    expired = 0
    for request in requests.list_pending():
        booking = bookings.get(request.booking_id)
        if (
            booking is not None
            and booking.state == BookingState.CONFIRMED
            and now < booking.start_time
        ):
            continue
        requests.save(replace(request, status="expired", updated_at=now))
        change_transitions.append(
            ShiftChangeTransition(
                transition_id=str(uuid4()),
                request_id=request.request_id,
                from_status=request.status,
                to_status="expired",
                occurred_at=now,
                actor_role="system",
            )
        )
        expired += 1
    return expired

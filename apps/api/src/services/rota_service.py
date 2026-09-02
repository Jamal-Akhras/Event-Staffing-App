from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import date, datetime, timedelta
from typing import Any
from uuid import uuid4
from zoneinfo import ZoneInfo

from sqlalchemy.exc import IntegrityError

from apps.api.src.models.booking_transition import BookingTransition
from apps.api.src.models.rota_publication import RotaPublication
from apps.api.src.models.shift import Shift
from apps.api.src.models.worker_relationship import EMPLOYED_TYPES
from apps.api.src.repositories.application_repository import ApplicationRepository
from apps.api.src.repositories.booking_allocator import BookingAllocator, OverlappingBookingError
from apps.api.src.repositories.booking_repository import BookingRepository
from apps.api.src.repositories.booking_transition_repository import BookingTransitionRepository
from apps.api.src.repositories.in_memory_rota_publication_repository import DuplicateRevisionError
from apps.api.src.repositories.rota_publication_repository import RotaPublicationRepository
from apps.api.src.repositories.shift_repository import ShiftRepository
from apps.api.src.repositories.worker_relationship_repository import WorkerRelationshipRepository
from apps.api.src.schemas_recovery import CancellationRequest
from apps.api.src.services.booking_lifecycle_service import BookingLifecycleService
from apps.api.src.services.errors import ConflictError, NotFoundError, ValidationError
from apps.api.src.services.escalation_service import EscalationService
from apps.api.src.services.outbox_publisher import OutboxPublisher
from apps.api.src.repositories.account_repository import AccountRepository
from apps.api.src.repositories.market_repository import MarketRepository
from apps.api.src.services.rota_diff import _diff, _entry, _normalize
from apps.api.src.services.rota_week import local_day, venue_timezone, week_window
from packages.domain.src.booking import Booking
from packages.domain.src.booking_state import BookingState


@dataclass(frozen=True)
class PublishOutcome:
    publication: RotaPublication
    changes: list[dict[str, Any]]
    booked_worker_ids: list[str]
    offered_worker_ids: list[str]


class RotaService:
    def __init__(
        self,
        shifts: ShiftRepository,
        bookings: BookingRepository,
        applications: ApplicationRepository,
        allocator: BookingAllocator,
        publications: RotaPublicationRepository,
        relationships: WorkerRelationshipRepository,
        transitions: BookingTransitionRepository,
        lifecycle: BookingLifecycleService,
        escalations: EscalationService,
        outbox: OutboxPublisher,
        accounts: AccountRepository,
        markets: MarketRepository,
    ) -> None:
        self._shifts = shifts
        self._bookings = bookings
        self._applications = applications
        self._allocator = allocator
        self._publications = publications
        self._relationships = relationships
        self._transitions = transitions
        self._lifecycle = lifecycle
        self._escalations = escalations
        self._outbox = outbox
        self._accounts = accounts
        self._markets = markets

    def publish(self, venue_id: str, week_start: date, actor_user_id: str, now: datetime) -> PublishOutcome:
        zone = self._zone_for(venue_id)
        window_start, window_end = week_window(week_start, zone)
        week_shifts = [
            shift
            for shift in self._shifts.list_in_range(venue_id, window_start, window_end)
            if shift.status != "cancelled"
        ]
        drafts = [shift for shift in week_shifts if shift.rota_state == "draft"]

        plans = []
        for draft in drafts:
            relationship = self._relationships.get_for_venue_worker(venue_id, draft.assigned_worker_id)
            if relationship is None or relationship.status != "active":
                raise ValidationError(
                    f"{draft.role} on {local_day(draft.start_time, zone)} is assigned to someone "
                    f"without an active relationship (shift {draft.shift_id}). Reassign it, then publish."
                )
            employed = relationship.relationship_type in EMPLOYED_TYPES
            if employed:
                try:
                    self._allocator.check_availability(
                        draft.assigned_worker_id, draft.start_time, draft.end_time, draft.shift_id
                    )
                except OverlappingBookingError as exc:
                    raise ValidationError(
                        f"{draft.role} (shift {draft.shift_id}) overlaps a booking its assignee "
                        f"already has on shift {exc.clashing_shift_id}."
                    ) from exc
                for other, other_employed in plans:
                    if (
                        other_employed
                        and other.assigned_worker_id == draft.assigned_worker_id
                        and other.start_time < draft.end_time
                        and other.end_time > draft.start_time
                    ):
                        raise ValidationError(
                            f"{draft.role} (shift {draft.shift_id}) overlaps draft shift "
                            f"{other.shift_id} for the same person."
                        )
            plans.append((draft, employed))

        booked: list[str] = []
        offered: list[str] = []
        for draft, employed in plans:
            if employed:
                self._book_employed(draft, actor_user_id, now)
                booked.append(draft.assigned_worker_id)
            else:
                published = replace(draft, rota_state="published")
                self._shifts.save(self._escalations.stamp_new_shift(published, now))
                offered.append(draft.assigned_worker_id)

        synced = self._sync_booking_times(venue_id, window_start, window_end, actor_user_id, now)
        outcome = self._mint_revision(venue_id, week_start, actor_user_id, now)
        self._notify(outcome, booked, exclude=synced)
        return PublishOutcome(
            publication=outcome.publication,
            changes=outcome.changes,
            booked_worker_ids=booked,
            offered_worker_ids=offered,
        )

    def update_times(
        self, venue_id: str, shift_id: str, start_time: datetime, end_time: datetime,
        actor_user_id: str, now: datetime,
    ) -> Shift:
        if end_time <= start_time:
            raise ValidationError("The end time has to be after the start time.")
        shift = self._published_shift(venue_id, shift_id)
        live = self._live_bookings(shift_id)
        if len(live) > 1:
            raise ValidationError("This shift has several bookings: reassign or cancel instead.")

        if not live:
            pending = [a for a in self._applications.list_by_shift(shift_id) if a.status == "applied"]
            if pending:
                raise ValidationError("This shift has pending applications: decide them first.")
            updated = replace(shift, start_time=start_time, end_time=end_time)
            self._shifts.save(self._escalations.stamp_new_shift(updated, now))
        else:
            booking = live[0]
            if booking.state != BookingState.CONFIRMED:
                raise ValidationError("This shift has already started: adjust hours on the timesheet instead.")
            try:
                self._allocator.check_availability(booking.worker_id, start_time, end_time, shift_id)
            except OverlappingBookingError as exc:
                raise ValidationError(
                    f"The new times overlap a booking this worker already has on shift {exc.clashing_shift_id}."
                ) from exc
            self._shifts.save(replace(shift, start_time=start_time, end_time=end_time, updated_at=now))
            self._bookings.save(replace(booking, start_time=start_time, end_time=end_time))
            self._append_transition(
                booking.booking_id, "confirmed", "confirmed", actor_user_id, now,
                "shift_details_changed",
                {"previous_start": shift.start_time.isoformat(), "previous_end": shift.end_time.isoformat(),
                 "start": start_time.isoformat(), "end": end_time.isoformat()},
            )
            self._notify_worker(
                booking.worker_id, shift, "rota.times_changed", "Your shift times changed",
                f"{shift.role} now runs {start_time:%H:%M}–{end_time:%H:%M} UTC.", booked=True,
            )

        outcome = self._mint_revision(venue_id, self._week_of(shift), actor_user_id, now)
        self._notify(outcome, [b.worker_id for b in live], exclude={b.worker_id for b in live})
        return self._shifts.get(shift_id)

    def reassign(
        self, venue_id: str, shift_id: str, new_worker_id: str, actor_user_id: str, now: datetime
    ) -> Shift:
        shift = self._published_shift(venue_id, shift_id)
        relationship = self._relationships.get_for_venue_worker(venue_id, new_worker_id)
        if relationship is None or relationship.status != "active":
            raise ValidationError("That worker does not have an active relationship with your venue.")

        live = self._live_bookings(shift_id)
        if len(live) > 1:
            raise ValidationError("This shift has several bookings: cancel individually instead.")
        if live and live[0].worker_id == new_worker_id:
            raise ValidationError("That worker is already booked on this shift.")
        if any(b.worker_id == new_worker_id for b in self._bookings.list_by_shift(shift_id)):
            raise ValidationError("That worker has already held a booking on this shift.")
        if live and live[0].state != BookingState.CONFIRMED:
            raise ValidationError("This shift has already started.")
        try:
            self._allocator.check_availability(new_worker_id, shift.start_time, shift.end_time, shift_id)
        except OverlappingBookingError as exc:
            raise ValidationError(
                f"That worker already has an overlapping booking on shift {exc.clashing_shift_id}."
            ) from exc

        drafted = self._shifts.save(
            replace(shift, rota_state="draft", origin="assigned", assigned_worker_id=new_worker_id,
                    offer_pool_at=None, publish_market_at=None, updated_at=now)
        )
        if live:
            self._lifecycle.transition(
                live[0].booking_id,
                BookingState.CANCELLED_BY_OPERATOR,
                CancellationRequest(reason="The rota was changed and this shift was reassigned.", now=now),
                actor_user_id,
                actor_role="operator",
            )
            drafted = self._shifts.get(shift_id)

        employed = relationship.relationship_type in EMPLOYED_TYPES
        if employed:
            self._book_employed(drafted, actor_user_id, now)
        else:
            self._shifts.save(
                self._escalations.stamp_new_shift(replace(drafted, rota_state="published"), now)
            )
            self._notify_worker(
                new_worker_id, drafted, "shift.offered_to_pool", "A shift was offered to you",
                f"{drafted.role} is yours to take.", booked=False,
            )

        outcome = self._mint_revision(venue_id, self._week_of(shift), actor_user_id, now)
        exclude = {live[0].worker_id} if live else set()
        if not employed:
            exclude.add(new_worker_id)
        self._notify(outcome, [new_worker_id] if employed else [], exclude=exclude)
        return self._shifts.get(shift_id)

    def remove(
        self, venue_id: str, shift_id: str, reason: str, actor_user_id: str, now: datetime
    ) -> Shift:
        shift = self._published_shift(venue_id, shift_id)
        live = self._live_bookings(shift_id)
        self._shifts.save(
            replace(shift, status="cancelled", cancelled_at=now, cancellation_reason=reason,
                    cancelled_by_user_id=actor_user_id, updated_at=now)
        )
        for booking in live:
            if booking.state == BookingState.CONFIRMED:
                self._lifecycle.transition(
                    booking.booking_id,
                    BookingState.CANCELLED_BY_OPERATOR,
                    CancellationRequest(reason=reason, now=now),
                    actor_user_id,
                    actor_role="operator",
                )
        outcome = self._mint_revision(venue_id, self._week_of(shift), actor_user_id, now)
        self._notify(outcome, [], exclude={booking.worker_id for booking in live})
        return self._shifts.get(shift_id)

    def publications_for_week(self, venue_id: str, week_start: date) -> list[tuple[RotaPublication, list[dict[str, Any]]]]:
        revisions = self._publications.list_for_week(venue_id, week_start)
        result = []
        previous: list[dict[str, Any]] = []
        for publication in revisions:
            result.append((publication, _diff(previous, publication.assignments)))
            previous = publication.assignments
        return result

    def _book_employed(self, draft: Shift, actor_user_id: str, now: datetime) -> None:
        allocated = self._allocator.allocate(
            draft.shift_id, draft.assigned_worker_id, now, str(uuid4()), attendance_mode="employed"
        )
        self._append_transition(
            allocated.booking.booking_id, None, "confirmed", actor_user_id, now, "rota_published",
            {"shift_id": draft.shift_id, "worker_id": draft.assigned_worker_id},
        )
        fresh = self._shifts.get(draft.shift_id)
        self._shifts.save(replace(fresh, rota_state="published", updated_at=now))

    def _sync_booking_times(
        self, venue_id: str, window_start: datetime, window_end: datetime, actor_user_id: str, now: datetime
    ) -> set[str]:
        synced: set[str] = set()
        for shift in self._shifts.list_in_range(venue_id, window_start, window_end):
            if shift.status == "cancelled" or shift.rota_state != "published":
                continue
            for booking in self._live_bookings(shift.shift_id):
                if booking.state != BookingState.CONFIRMED:
                    continue
                if booking.start_time == shift.start_time and booking.end_time == shift.end_time:
                    continue
                self._bookings.save(
                    replace(booking, start_time=shift.start_time, end_time=shift.end_time)
                )
                self._append_transition(
                    booking.booking_id, "confirmed", "confirmed", actor_user_id, now,
                    "shift_details_changed",
                    {"previous_start": booking.start_time.isoformat(),
                     "previous_end": booking.end_time.isoformat(),
                     "start": shift.start_time.isoformat(), "end": shift.end_time.isoformat()},
                )
                self._notify_worker(
                    booking.worker_id, shift, "rota.times_changed", "Your shift times changed",
                    f"{shift.role} now runs {shift.start_time:%H:%M}–{shift.end_time:%H:%M} UTC.",
                    booked=True,
                )
                synced.add(booking.worker_id)
        return synced

    def _mint_revision(self, venue_id: str, week_start: date, actor_user_id: str, now: datetime) -> PublishOutcome:
        snapshot = self._snapshot(venue_id, week_start, self._zone_for(venue_id))
        previous = self._publications.latest_for_week(venue_id, week_start)
        previous_entries = previous.assignments if previous else []
        if previous is not None and _normalize(previous_entries) == _normalize(snapshot):
            return PublishOutcome(previous, [], [], [])
        publication = RotaPublication(
            publication_id=str(uuid4()),
            venue_id=venue_id,
            week_start=week_start,
            revision=(previous.revision + 1) if previous else 1,
            published_at=now,
            published_by_user_id=actor_user_id,
            assignments=snapshot,
        )
        try:
            self._publications.save(publication)
        except (IntegrityError, DuplicateRevisionError) as exc:
            raise ConflictError("The rota was published concurrently: reload and try again.") from exc
        return PublishOutcome(publication, _diff(previous_entries, snapshot), [], [])

    def _snapshot(self, venue_id: str, week_start: date, zone: ZoneInfo) -> list[dict[str, Any]]:
        window_start, window_end = week_window(week_start, zone)
        entries: dict[tuple[str, str], dict[str, Any]] = {}
        for shift in self._shifts.list_in_range(venue_id, window_start, window_end):
            if shift.status == "cancelled" or shift.rota_state != "published":
                continue
            if shift.origin == "assigned" and shift.assigned_worker_id:
                entries[(shift.shift_id, shift.assigned_worker_id)] = _entry(shift, shift.assigned_worker_id)
            for booking in self._live_bookings(shift.shift_id):
                entries[(shift.shift_id, booking.worker_id)] = _entry(shift, booking.worker_id)
        return sorted(entries.values(), key=lambda item: (item["shift_id"], item["worker_id"]))

    def _notify(
        self,
        outcome: PublishOutcome,
        booked_worker_ids: list[str],
        exclude: set[str] | None = None,
    ) -> None:
        exclude = exclude or set()
        if outcome.publication.revision == 1 and not outcome.changes:
            targets = {entry["worker_id"] for entry in outcome.publication.assignments}
        else:
            targets = {
                worker_id
                for change in outcome.changes
                for worker_id in (change.get("worker_id"), change.get("previous_worker_id"))
                if worker_id
            }
        for worker_id in sorted(targets - exclude):
            entry = next(
                (e for e in outcome.publication.assignments if e["worker_id"] == worker_id), None
            )
            body = "Open the app to see your week." if entry else "One of your shifts changed."
            self._outbox.publish_notification(
                event_type="rota.published",
                aggregate_type="rota_publication",
                aggregate_id=f"{outcome.publication.publication_id}:{worker_id}",
                recipient_kind="worker",
                recipient_id=worker_id,
                category="shift_changes",
                title="Your rota was published",
                body=body,
                action_kind="booking" if worker_id in booked_worker_ids or entry else "shift",
                action_entity_id=entry["shift_id"] if entry else outcome.publication.publication_id,
            )

    def _notify_worker(
        self, worker_id: str, shift: Shift, event_type: str, title: str, body: str, booked: bool
    ) -> None:
        self._outbox.publish_notification(
            event_type=event_type,
            aggregate_type="shift",
            aggregate_id=f"{shift.shift_id}:{worker_id}",
            recipient_kind="worker",
            recipient_id=worker_id,
            category="shift_changes",
            title=title,
            body=body,
            action_kind="booking" if booked else "shift",
            action_entity_id=shift.shift_id,
        )

    def _append_transition(
        self, booking_id: str, from_state: str | None, to_state: str, actor_user_id: str,
        now: datetime, reason_code: str, context: dict[str, Any],
    ) -> None:
        self._transitions.append(
            BookingTransition(
                transition_id=str(uuid4()),
                booking_id=booking_id,
                from_state=from_state,
                to_state=to_state,
                occurred_at=now,
                actor_user_id=actor_user_id,
                actor_role="operator",
                reason_code=reason_code,
                context=context,
            )
        )

    def _published_shift(self, venue_id: str, shift_id: str) -> Shift:
        shift = self._shifts.get(shift_id)
        if shift is None or shift.account_id != venue_id:
            raise NotFoundError("That shift was not found.")
        if shift.status == "cancelled":
            raise ValidationError("That shift is cancelled.")
        if shift.rota_state != "published":
            raise ValidationError("That shift is still a draft: edit it directly and publish the week.")
        return shift

    def _zone_for(self, venue_id: str) -> ZoneInfo:
        return venue_timezone(venue_id, self._accounts, self._markets)

    def _live_bookings(self, shift_id: str) -> list[Booking]:
        live_states = {
            BookingState.CONFIRMED,
            BookingState.CHECKED_IN,
            BookingState.CHECKED_OUT,
            BookingState.APPROVED,
            BookingState.PAID,
        }
        return [b for b in self._bookings.list_by_shift(shift_id) if b.state in live_states]

    def _week_of(self, shift: Shift) -> date:
        day = local_day(shift.start_time, self._zone_for(shift.account_id))
        for offset in range(7):
            candidate = day - timedelta(days=offset)
            if self._publications.latest_for_week(shift.account_id, candidate) is not None:
                return candidate
        return day

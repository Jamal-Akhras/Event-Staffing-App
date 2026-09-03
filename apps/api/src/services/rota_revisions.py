from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Any
from uuid import uuid4
from zoneinfo import ZoneInfo

from sqlalchemy.exc import IntegrityError

from apps.api.src.models.rota_publication import RotaPublication
from apps.api.src.models.shift import Shift
from apps.api.src.repositories.account_repository import AccountRepository
from apps.api.src.repositories.booking_repository import BookingRepository
from apps.api.src.repositories.in_memory_rota_publication_repository import DuplicateRevisionError
from apps.api.src.repositories.market_repository import MarketRepository
from apps.api.src.repositories.rota_publication_repository import RotaPublicationRepository
from apps.api.src.services.errors import ConflictError
from apps.api.src.services.outbox_publisher import OutboxPublisher
from apps.api.src.services.rota_diff import _diff, _entry, _normalize
from apps.api.src.services.rota_week import local_day, venue_timezone, week_window
from packages.domain.src.booking import Booking
from packages.domain.src.booking_state import BookingState

LIVE_STATES = {
    BookingState.CONFIRMED,
    BookingState.CHECKED_IN,
    BookingState.CHECKED_OUT,
    BookingState.APPROVED,
    BookingState.PAID,
}


def live_bookings(bookings: BookingRepository, shift_id: str) -> list[Booking]:
    return [b for b in bookings.list_by_shift(shift_id) if b.state in LIVE_STATES]


@dataclass(frozen=True)
class PublishOutcome:
    publication: RotaPublication
    changes: list[dict[str, Any]]
    booked_worker_ids: list[str]
    offered_worker_ids: list[str]


class RotaRevisionService:
    def __init__(
        self,
        shifts,
        bookings: BookingRepository,
        publications: RotaPublicationRepository,
        outbox: OutboxPublisher,
        accounts: AccountRepository,
        markets: MarketRepository,
    ) -> None:
        self._shifts = shifts
        self._bookings = bookings
        self._publications = publications
        self._outbox = outbox
        self._accounts = accounts
        self._markets = markets

    def zone_for(self, venue_id: str) -> ZoneInfo:
        return venue_timezone(venue_id, self._accounts, self._markets)

    def week_of(self, shift: Shift) -> date:
        day = local_day(shift.start_time, self.zone_for(shift.account_id))
        for offset in range(7):
            candidate = day - timedelta(days=offset)
            if self._publications.latest_for_week(shift.account_id, candidate) is not None:
                return candidate
        return day

    def publications_for_week(
        self, venue_id: str, week_start: date
    ) -> list[tuple[RotaPublication, list[dict[str, Any]]]]:
        revisions = self._publications.list_for_week(venue_id, week_start)
        result = []
        previous: list[dict[str, Any]] = []
        for publication in revisions:
            result.append((publication, _diff(previous, publication.assignments)))
            previous = publication.assignments
        return result

    def mint(self, venue_id: str, week_start: date, actor_user_id: str, now: datetime) -> PublishOutcome:
        snapshot = self._snapshot(venue_id, week_start, self.zone_for(venue_id))
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

    def notify(self, outcome: PublishOutcome, exclude: set[str] | None = None) -> None:
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
            booking = next(
                (
                    candidate
                    for candidate in live_bookings(self._bookings, entry["shift_id"])
                    if candidate.worker_id == worker_id
                ),
                None,
            ) if entry else None
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
                action_kind="booking" if booking is not None else "shift",
                action_entity_id=(
                    booking.booking_id
                    if booking is not None
                    else entry["shift_id"] if entry else outcome.publication.publication_id
                ),
            )

    def _snapshot(self, venue_id: str, week_start: date, zone: ZoneInfo) -> list[dict[str, Any]]:
        window_start, window_end = week_window(week_start, zone)
        entries: dict[tuple[str, str], dict[str, Any]] = {}
        for shift in self._shifts.list_in_range(venue_id, window_start, window_end):
            if shift.status == "cancelled" or shift.rota_state != "published":
                continue
            if shift.origin == "assigned" and shift.assigned_worker_id:
                entries[(shift.shift_id, shift.assigned_worker_id)] = _entry(shift, shift.assigned_worker_id)
            for booking in live_bookings(self._bookings, shift.shift_id):
                entries[(shift.shift_id, booking.worker_id)] = _entry(shift, booking.worker_id)
        return sorted(entries.values(), key=lambda item: (item["shift_id"], item["worker_id"]))

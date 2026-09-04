from __future__ import annotations

from zoneinfo import ZoneInfo

from apps.api.src.repositories.in_memory_application_repository import InMemoryApplicationRepository
from apps.api.src.repositories.in_memory_organisation_repository import InMemoryOrganisationRepository
from apps.api.src.repositories.in_memory_shift_repository import InMemoryShiftRepository
from apps.api.src.repositories.in_memory_worker_feed_state_repository import InMemoryWorkerFeedStateRepository
from apps.api.src.repositories.in_memory_worker_relationship_repository import InMemoryWorkerRelationshipRepository
from apps.api.src.models.worker_feed_query import WorkerFeedItem, WorkerFeedQuery


class InMemoryWorkerFeedQueryRepository:
    def __init__(
        self,
        shifts: InMemoryShiftRepository,
        organisations: InMemoryOrganisationRepository,
        applications: InMemoryApplicationRepository,
        feed_states: InMemoryWorkerFeedStateRepository,
        relationships: InMemoryWorkerRelationshipRepository,
        boosts=None,
    ) -> None:
        self._shifts = shifts
        self._organisations = organisations
        self._applications = applications
        self._feed_states = feed_states
        self._relationships = relationships
        self._boosts = boosts

    def _bucket(self, shift) -> int:
        if shift.origin in ("assigned", "team"):
            return 0
        if shift.origin == "pool":
            return 1
        return 2

    def _boost_tier(self, shift) -> str | None:
        if self._boosts is None:
            return None
        boost = self._boosts.get_active_for_shift(shift.shift_id)
        return boost.tier if boost is not None else None

    def _is_related(self, shift, worker_id: str) -> bool:
        relationship = self._relationships.get_for_venue_worker(shift.account_id or "", worker_id)
        return (
            relationship is not None
            and relationship.status in ("active", "invited")
            and relationship.relationship_type != "one_off"
        )

    def _reaches_worker(self, shift, worker_id: str, marketplace_enabled: bool) -> bool:
        if shift.origin == "market":
            return marketplace_enabled or self._is_related(shift, worker_id)
        if shift.origin == "assigned":
            return shift.assigned_worker_id == worker_id
        if shift.origin == "team":
            relationship = self._relationships.get_for_venue_worker(shift.account_id or "", worker_id)
            return (
                relationship is not None
                and relationship.status in ("active", "invited")
                and relationship.relationship_type in ("permanent", "part_time", "bank")
            )
        return self._is_related(shift, worker_id)

    def list_page(self, query: WorkerFeedQuery) -> list[WorkerFeedItem]:
        local_zone = ZoneInfo(query.timezone)
        normalized_search = (query.search or "").casefold()
        items: list[WorkerFeedItem] = []
        for shift in self._shifts.list_recent(10_000):
            venue = self._organisations.get_venue(shift.account_id or "")
            if venue is None or venue.market_id != query.market_id:
                continue
            if shift.status != "open" or shift.start_time <= query.now:
                continue
            if shift.rota_state == "draft" or shift.needs_attention:
                continue
            if shift.workers_filled >= shift.workers_needed:
                continue
            if not self._reaches_worker(shift, query.worker_id, query.marketplace_enabled):
                continue
            if self._feed_states.get(query.worker_id, shift.shift_id) is not None:
                continue
            if self._applications.find_by_worker_and_shift(query.worker_id, shift.shift_id) is not None:
                continue
            if normalized_search:
                haystack = f"{shift.role} {shift.location} {venue.name}".casefold()
                if normalized_search not in haystack:
                    continue
            if query.minimum_pay is not None and shift.pay_rate < query.minimum_pay:
                continue
            local_start = shift.start_time.astimezone(local_zone)
            if query.timing == "today" and not (
                query.today_start <= shift.start_time < query.today_end
            ):
                continue
            if query.timing == "weekend" and local_start.weekday() < 5:
                continue
            bucket = self._bucket(shift)
            if query.position and (bucket, shift.start_time, shift.shift_id) <= (
                query.position.bucket,
                query.position.start_time,
                query.position.shift_id,
            ):
                continue
            tier = self._boost_tier(shift)
            items.append(
                WorkerFeedItem(
                    shift=shift, venue=venue, bucket=bucket,
                    boosted=tier is not None, boost_tier=tier,
                )
            )
        items.sort(key=lambda item: (item.bucket, item.shift.start_time, item.shift.shift_id))
        return items[: query.limit + 1]

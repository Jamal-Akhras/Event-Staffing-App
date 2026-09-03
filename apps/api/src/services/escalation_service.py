from __future__ import annotations

from dataclasses import replace
from datetime import datetime
from typing import Callable

from apps.api.src.models.shift import Shift
from apps.api.src.models.worker_relationship import EMPLOYED_TYPES, WorkerRelationship
from apps.api.src.repositories.account_repository import AccountRepository
from apps.api.src.repositories.shift_repository import ShiftRepository
from apps.api.src.repositories.worker_relationship_repository import WorkerRelationshipRepository
from apps.api.src.services.errors import NotFoundError, ValidationError
from apps.api.src.services.escalation_policy import RUNG_ORDER, plan_rungs, policy_from_venue
from apps.api.src.services.outbox_publisher import OutboxPublisher


class EscalationService:
    def __init__(
        self,
        shifts: ShiftRepository,
        relationships: WorkerRelationshipRepository,
        accounts: AccountRepository,
        outbox: OutboxPublisher,
    ) -> None:
        self._shifts = shifts
        self._relationships = relationships
        self._accounts = accounts
        self._outbox = outbox

    def stamp_new_shift(self, shift: Shift, now: datetime) -> Shift:
        policy = self._policy_for(shift.account_id)
        assigned = shift.assigned_worker_id is not None
        billable = not self._assigned_to_employee(shift)
        if shift.rota_state == "draft":
            return replace(
                shift, origin="assigned", billable=billable,
                offer_team_at=None, offer_pool_at=None, publish_market_at=None,
            )
        has_team = self._has_team(shift.account_id)
        has_pool = self._has_people(shift.account_id)
        if assigned:
            first = "assigned"
        else:
            first = self._first_open_rung(policy, has_team, has_pool)
            if first is None:
                raise ValidationError(
                    "This shift has nowhere to go: turn a rung on in Settings or assign someone."
                )
        stamps = plan_rungs(shift.start_time, now, policy, first, has_team, has_pool)
        keep = first != "market"
        return replace(
            shift,
            origin=first,
            billable=billable,
            offer_team_at=stamps.offer_team_at if keep else None,
            offer_pool_at=stamps.offer_pool_at if keep else None,
            publish_market_at=stamps.publish_market_at if keep else None,
        )

    def restart_ladder(self, shift_id: str, now: datetime) -> Shift | None:
        shift = self._shifts.get(shift_id)
        if (
            shift is None
            or shift.status != "open"
            or shift.rota_state != "published"
            or shift.needs_attention
            or shift.start_time <= now
        ):
            return None
        policy = self._policy_for(shift.account_id)
        has_team = self._has_team(shift.account_id)
        has_pool = self._has_people(shift.account_id)
        first = self._first_open_rung(policy, has_team, has_pool)
        if first is not None:
            stamps = plan_rungs(shift.start_time, now, policy, first, has_team, has_pool)
            keep = first != "market"
            return self._shifts.save(
                replace(
                    shift,
                    origin=first,
                    assigned_worker_id=None,
                    billable=True,
                    offer_team_at=stamps.offer_team_at if keep else None,
                    offer_pool_at=stamps.offer_pool_at if keep else None,
                    publish_market_at=stamps.publish_market_at if keep else None,
                    updated_at=now,
                )
            )
        parked = self._shifts.save(
            replace(
                shift,
                origin="pool",
                assigned_worker_id=None,
                billable=True,
                needs_attention=True,
                offer_team_at=None,
                offer_pool_at=None,
                publish_market_at=None,
                updated_at=now,
            )
        )
        self._notify_venue_attention(parked)
        return parked

    def sweep(self, now: datetime) -> list[Shift]:
        moved = []
        for shift in self._shifts.list_due_for_escalation(now):
            target = self._next_stamped_rung(shift)
            if target is None:
                continue
            moved.append(self._advance(shift, target, now, "Reached the next step."))
        return moved

    def advance_now(self, shift_id: str, venue_id: str, target: str, now: datetime) -> Shift:
        shift = self._shifts.get(shift_id)
        if shift is None or shift.account_id != venue_id:
            raise NotFoundError("That shift was not found.")
        if target not in ("team", "pool", "market"):
            raise ValidationError("A shift can only be moved to your team, your pool or the open market.")
        if shift.origin == "market":
            raise ValidationError("This shift is already on the open market.")
        if RUNG_ORDER.index(target) <= RUNG_ORDER.index(shift.origin):
            raise ValidationError("A shift only moves outward: team, then pool, then the open market.")
        if shift.needs_attention:
            shift = self._shifts.save(replace(shift, needs_attention=False, updated_at=now))
        return self._advance(shift, target, now, "Moved by the venue.")

    def _advance(self, shift: Shift, target: str, now: datetime, reason: str) -> Shift:
        previous = shift.origin
        market = target == "market"
        moved = self._shifts.save(
            replace(
                shift,
                origin=target,
                assigned_worker_id=None,
                billable=True,
                offer_team_at=None if market else shift.offer_team_at,
                offer_pool_at=None if market else shift.offer_pool_at,
                publish_market_at=None if market else shift.publish_market_at,
                updated_at=now,
            )
        )
        if target == "team":
            self._notify_audience(moved, reason, self._is_team_member)
        elif target == "pool":
            newly = self._is_pool_member if previous == "team" else self._is_private_member
            self._notify_audience(moved, reason, newly)
        return moved

    def _next_stamped_rung(self, shift: Shift) -> str | None:
        stamps = {
            "team": shift.offer_team_at,
            "pool": shift.offer_pool_at,
            "market": shift.publish_market_at,
        }
        for rung in RUNG_ORDER[RUNG_ORDER.index(shift.origin) + 1:]:
            if stamps[rung] is not None:
                return rung
        return None

    def _first_open_rung(self, policy, has_team: bool, has_pool: bool) -> str | None:
        if policy.offers_team and has_team:
            return "team"
        if policy.offers_pool and has_pool:
            return "pool"
        if policy.reaches_market:
            return "market"
        return None

    def _notify_venue_attention(self, shift: Shift) -> None:
        if not shift.account_id:
            return
        self._outbox.publish_notification(
            event_type="shift.needs_attention",
            aggregate_type="shift",
            aggregate_id=shift.shift_id,
            recipient_kind="venue",
            recipient_id=shift.account_id,
            category="shift_changes",
            title="A slot needs your attention",
            body=f"{shift.role} has no one to go to: assign someone or move it on manually.",
            action_kind="shift",
            action_entity_id=shift.shift_id,
        )

    def _notify_audience(
        self, shift: Shift, reason: str,
        included: Callable[[WorkerRelationship], bool],
    ) -> None:
        if not shift.account_id:
            return
        venue = self._accounts.get(shift.account_id)
        for relationship in self._relationships.list_for_venue(shift.account_id):
            if relationship.status not in ("active", "invited") or not included(relationship):
                continue
            self._outbox.publish_notification(
                event_type="shift.offered_to_pool",
                aggregate_type="shift",
                aggregate_id=shift.shift_id,
                recipient_kind="worker",
                recipient_id=relationship.worker_id,
                category="shift_changes",
                title=f"{venue.name if venue else 'A venue'} needs a {shift.role}",
                body=reason,
                action_kind="shift",
                action_entity_id=shift.shift_id,
            )

    @staticmethod
    def _is_team_member(relationship: WorkerRelationship) -> bool:
        return relationship.relationship_type in EMPLOYED_TYPES

    @staticmethod
    def _is_pool_member(relationship: WorkerRelationship) -> bool:
        return relationship.relationship_type == "pool"

    @staticmethod
    def _is_private_member(relationship: WorkerRelationship) -> bool:
        return relationship.relationship_type != "one_off"

    def _assigned_to_employee(self, shift: Shift) -> bool:
        if shift.assigned_worker_id is None or not shift.account_id:
            return False
        relationship = self._relationships.get_for_venue_worker(shift.account_id, shift.assigned_worker_id)
        return (
            relationship is not None
            and relationship.status == "active"
            and relationship.relationship_type in EMPLOYED_TYPES
        )

    def _has_team(self, venue_id: str | None) -> bool:
        if not venue_id:
            return False
        return any(
            relationship.relationship_type in EMPLOYED_TYPES
            and relationship.status in ("active", "invited")
            for relationship in self._relationships.list_for_venue(venue_id)
        )

    def _has_people(self, venue_id: str | None) -> bool:
        if not venue_id:
            return False
        return any(
            relationship.relationship_type != "one_off"
            and relationship.status in ("active", "invited")
            for relationship in self._relationships.list_for_venue(venue_id)
        )

    def _policy_for(self, venue_id: str | None):
        venue = self._accounts.get(venue_id) if venue_id else None
        return policy_from_venue(venue.escalation_policy if venue else None)

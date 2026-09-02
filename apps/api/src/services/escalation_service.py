from __future__ import annotations

from dataclasses import replace
from datetime import datetime

from apps.api.src.models.shift import Shift
from apps.api.src.models.worker_relationship import EMPLOYED_TYPES
from apps.api.src.repositories.account_repository import AccountRepository
from apps.api.src.repositories.shift_repository import ShiftRepository
from apps.api.src.repositories.worker_relationship_repository import WorkerRelationshipRepository
from apps.api.src.services.errors import NotFoundError, ValidationError
from apps.api.src.services.escalation_policy import next_timestamps, policy_from_venue
from apps.api.src.services.outbox_publisher import OutboxPublisher

NEXT_RUNG = {"assigned": "pool", "pool": "market"}


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
                shift, origin="assigned", billable=billable, offer_pool_at=None, publish_market_at=None
            )
        private_rung = policy.offers_pool and self._has_people(shift.account_id)
        if not assigned and not private_rung and not policy.reaches_market:
            raise ValidationError(
                "This shift has nowhere to go: turn a rung on in Settings or assign someone."
            )
        stamps = next_timestamps(shift.start_time, now, policy, assigned)
        origin = "assigned" if assigned else ("pool" if private_rung else "market")
        return replace(
            shift,
            origin=origin,
            billable=billable,
            offer_pool_at=stamps.offer_pool_at if origin != "market" else None,
            publish_market_at=stamps.publish_market_at if origin != "market" else None,
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
        if policy.offers_pool and self._has_people(shift.account_id):
            stamps = next_timestamps(shift.start_time, now, policy, assigned=False)
            return self._shifts.save(
                replace(
                    shift,
                    origin="pool",
                    assigned_worker_id=None,
                    offer_pool_at=stamps.offer_pool_at,
                    publish_market_at=stamps.publish_market_at,
                    updated_at=now,
                )
            )
        if policy.reaches_market:
            return self._shifts.save(
                replace(shift, origin="market", assigned_worker_id=None, updated_at=now)
            )
        parked = self._shifts.save(
            replace(
                shift,
                origin="pool",
                assigned_worker_id=None,
                needs_attention=True,
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
            skip_pool = shift.origin == "assigned" and shift.offer_pool_at is None
            target = "market" if skip_pool else NEXT_RUNG[shift.origin]
            moved.append(self._advance(shift, target, now, "Reached the next step."))
        return moved

    def advance_now(self, shift_id: str, venue_id: str, target: str, now: datetime) -> Shift:
        shift = self._shifts.get(shift_id)
        if shift is not None and shift.needs_attention:
            shift = self._shifts.save(replace(shift, needs_attention=False, updated_at=now))
        if shift is None or shift.account_id != venue_id:
            raise NotFoundError("That shift was not found.")
        if target not in ("pool", "market"):
            raise ValidationError("A shift can only be moved to your pool or to the open market.")
        if NEXT_RUNG.get(shift.origin) is None:
            raise ValidationError("This shift is already on the open market.")
        return self._advance(shift, target, now, "Moved by the venue.")

    def _advance(self, shift: Shift, target: str, now: datetime, reason: str) -> Shift:
        moved = self._shifts.save(replace(shift, origin=target, updated_at=now))
        if target == "pool":
            self._notify_pool(moved, reason)
        return moved

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

    def _notify_pool(self, shift: Shift, reason: str) -> None:
        if not shift.account_id:
            return
        venue = self._accounts.get(shift.account_id)
        for relationship in self._relationships.list_for_venue(shift.account_id):
            if relationship.relationship_type == "one_off" or relationship.status not in ("active", "invited"):
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

    def _assigned_to_employee(self, shift: Shift) -> bool:
        if shift.assigned_worker_id is None or not shift.account_id:
            return False
        relationship = self._relationships.get_for_venue_worker(shift.account_id, shift.assigned_worker_id)
        return (
            relationship is not None
            and relationship.status == "active"
            and relationship.relationship_type in EMPLOYED_TYPES
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

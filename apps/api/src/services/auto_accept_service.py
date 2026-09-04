from __future__ import annotations

from datetime import datetime, timedelta
from decimal import Decimal
from uuid import uuid4

from apps.api.src.models.auto_accept import AutoAcceptAttempt, WorkerAutoAcceptRule
from apps.api.src.models.shift_offer import ShiftOffer
from apps.api.src.repositories.auto_accept_repository import (
    AutoAcceptAttemptRepository,
    DuplicateAutoAcceptAttemptError,
    WorkerAutoAcceptRuleRepository,
)
from apps.api.src.repositories.shift_offer_repository import ShiftOfferRepository
from apps.api.src.repositories.shift_repository import ShiftRepository
from apps.api.src.repositories.worker_relationship_repository import (
    WorkerRelationshipRepository,
)
from apps.api.src.services.certification_gate import MissingCertificationError
from apps.api.src.services.errors import NotFoundError, ServiceError, ValidationError
from apps.api.src.services.shift_offer_service import ShiftOfferService


class AutoAcceptService:
    def __init__(
        self,
        rules: WorkerAutoAcceptRuleRepository,
        attempts: AutoAcceptAttemptRepository,
        offers: ShiftOfferRepository,
        shifts: ShiftRepository,
        relationships: WorkerRelationshipRepository,
        offer_service: ShiftOfferService,
    ) -> None:
        self._rules = rules
        self._attempts = attempts
        self._offers = offers
        self._shifts = shifts
        self._relationships = relationships
        self._offer_service = offer_service

    def upsert_rule(
        self,
        worker_id: str,
        venue_id: str,
        enabled: bool,
        roles: list[str],
        minimum_rate: Decimal | None,
        minimum_notice_hours: int | None,
        now: datetime,
    ) -> WorkerAutoAcceptRule:
        existing = self._rules.get(worker_id, venue_id)
        relationship = self._relationships.get_for_venue_worker(venue_id, worker_id)
        if existing is None and relationship is None:
            raise NotFoundError("That venue relationship was not found.")
        if enabled and (
            relationship is None
            or relationship.status != "active"
            or relationship.relationship_type != "pool"
        ):
            raise ValidationError(
                "Auto-accept can only be enabled for an active pool relationship."
            )
        cleaned_roles = _clean_roles(roles)
        if minimum_rate is not None and minimum_rate < 0:
            raise ValidationError("Minimum rate cannot be negative.")
        if minimum_notice_hours is not None and minimum_notice_hours < 0:
            raise ValidationError("Minimum notice hours cannot be negative.")
        rule = WorkerAutoAcceptRule(
            rule_id=existing.rule_id if existing is not None else str(uuid4()),
            worker_id=worker_id,
            venue_id=venue_id,
            enabled=enabled,
            roles=cleaned_roles,
            minimum_rate=minimum_rate,
            minimum_notice_hours=minimum_notice_hours,
            version=existing.version + 1 if existing is not None else 1,
            created_at=existing.created_at if existing is not None else now,
            updated_at=now,
        )
        return self._rules.save(rule)

    def get_rule(self, worker_id: str, venue_id: str) -> WorkerAutoAcceptRule:
        rule = self._rules.get(worker_id, venue_id)
        if rule is None:
            raise NotFoundError("That auto-accept rule was not found.")
        return rule

    def list_rules(self, worker_id: str) -> list[WorkerAutoAcceptRule]:
        return self._rules.list_for_worker(worker_id)

    def delete_rule(self, worker_id: str, venue_id: str) -> None:
        if not self._rules.delete(worker_id, venue_id):
            raise NotFoundError("That auto-accept rule was not found.")

    def list_attempts(self, worker_id: str, limit: int) -> list[AutoAcceptAttempt]:
        return self._attempts.list_for_worker(worker_id, limit)

    def claim_candidates(self, now: datetime) -> list[ShiftOffer]:
        return self._offers.claim_pending_unexpired(now)

    def has_enabled_rule(self, offer: ShiftOffer) -> bool:
        rule = self._rules.get(offer.worker_id, offer.venue_id)
        return rule is not None and rule.enabled

    def evaluate_offer(self, offer: ShiftOffer, now: datetime) -> AutoAcceptAttempt:
        rule = self._rules.get(offer.worker_id, offer.venue_id)
        rule_version = rule.version if rule is not None else 0
        existing = self._attempts.get_for_offer_version(offer.offer_id, rule_version)
        if existing is not None:
            return existing
        snapshot = _snapshot(rule)
        if rule is None:
            return self._record(offer, None, 0, snapshot, now, "skipped", "no_rule")
        if not rule.enabled:
            return self._record(
                offer, rule.rule_id, rule.version, snapshot, now, "skipped", "rule_disabled"
            )
        shift = self._shifts.get(offer.shift_id)
        if shift is None:
            return self._record(
                offer,
                rule.rule_id,
                rule.version,
                snapshot,
                now,
                "failed",
                "That shift was not found.",
            )
        allowed_roles = {item.strip().casefold() for item in rule.roles}
        if allowed_roles and shift.role.strip().casefold() not in allowed_roles:
            return self._record(
                offer, rule.rule_id, rule.version, snapshot, now, "skipped", "role_mismatch"
            )
        if rule.minimum_rate is not None and shift.pay_rate < rule.minimum_rate:
            return self._record(
                offer,
                rule.rule_id,
                rule.version,
                snapshot,
                now,
                "skipped",
                "rate_below_minimum",
            )
        if (
            rule.minimum_notice_hours is not None
            and shift.start_time - now < timedelta(hours=rule.minimum_notice_hours)
        ):
            return self._record(
                offer,
                rule.rule_id,
                rule.version,
                snapshot,
                now,
                "skipped",
                "notice_too_short",
            )
        try:
            self._offer_service.accept(
                offer.offer_id,
                offer.worker_id,
                now,
                response_source="auto",
            )
        except MissingCertificationError:
            return self._record(
                offer,
                rule.rule_id,
                rule.version,
                snapshot,
                now,
                "skipped",
                "missing_certification",
            )
        except ServiceError as exc:
            return self._record(
                offer,
                rule.rule_id,
                rule.version,
                snapshot,
                now,
                "failed",
                str(exc),
            )
        return self._record(
            offer, rule.rule_id, rule.version, snapshot, now, "accepted", None
        )

    def _record(
        self,
        offer: ShiftOffer,
        rule_id: str | None,
        rule_version: int,
        snapshot: dict,
        now: datetime,
        outcome: str,
        reason: str | None,
    ) -> AutoAcceptAttempt:
        attempt = AutoAcceptAttempt(
            attempt_id=str(uuid4()),
            offer_id=offer.offer_id,
            rule_id=rule_id,
            rule_version=rule_version,
            rule_snapshot=snapshot,
            evaluated_at=now,
            outcome=outcome,
            reason=reason,
        )
        try:
            return self._attempts.save(attempt)
        except DuplicateAutoAcceptAttemptError:
            stored = self._attempts.get_for_offer_version(offer.offer_id, rule_version)
            if stored is None:
                raise RuntimeError("A duplicate auto-accept attempt could not be replayed.")
            return stored


def _clean_roles(roles: list[str]) -> list[str]:
    cleaned: list[str] = []
    seen: set[str] = set()
    for role in roles:
        value = role.strip()
        if not value:
            raise ValidationError("Auto-accept role names cannot be blank.")
        normalized = value.casefold()
        if normalized not in seen:
            cleaned.append(value)
            seen.add(normalized)
    return cleaned


def _snapshot(rule: WorkerAutoAcceptRule | None) -> dict:
    if rule is None:
        return {}
    return {
        "enabled": rule.enabled,
        "roles": list(rule.roles),
        "minimum_rate": str(rule.minimum_rate) if rule.minimum_rate is not None else None,
        "minimum_notice_hours": rule.minimum_notice_hours,
        "version": rule.version,
    }

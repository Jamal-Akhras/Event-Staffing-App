from __future__ import annotations

from apps.api.src.models.auto_accept import AutoAcceptAttempt, WorkerAutoAcceptRule
from apps.api.src.repositories.auto_accept_repository import (
    DuplicateAutoAcceptAttemptError,
)
from apps.api.src.repositories.shift_offer_repository import ShiftOfferRepository


class InMemoryWorkerAutoAcceptRuleRepository:
    def __init__(self) -> None:
        self._rules: dict[tuple[str, str], WorkerAutoAcceptRule] = {}

    def save(self, rule: WorkerAutoAcceptRule) -> WorkerAutoAcceptRule:
        self._rules[(rule.worker_id, rule.venue_id)] = rule
        return rule

    def get(self, worker_id: str, venue_id: str) -> WorkerAutoAcceptRule | None:
        return self._rules.get((worker_id, venue_id))

    def list_for_worker(self, worker_id: str) -> list[WorkerAutoAcceptRule]:
        return sorted(
            (rule for key, rule in self._rules.items() if key[0] == worker_id),
            key=lambda rule: rule.created_at,
        )

    def delete(self, worker_id: str, venue_id: str) -> bool:
        return self._rules.pop((worker_id, venue_id), None) is not None

    def clear(self) -> None:
        self._rules.clear()


class InMemoryAutoAcceptAttemptRepository:
    def __init__(self, offers: ShiftOfferRepository) -> None:
        self._offers = offers
        self._attempts: dict[tuple[str, int], AutoAcceptAttempt] = {}

    def save(self, attempt: AutoAcceptAttempt) -> AutoAcceptAttempt:
        key = (attempt.offer_id, attempt.rule_version)
        if key in self._attempts:
            raise DuplicateAutoAcceptAttemptError(
                f"Offer {attempt.offer_id} was already evaluated at rule version "
                f"{attempt.rule_version}."
            )
        if self._offers.get(attempt.offer_id) is None:
            raise ValueError(f"Offer {attempt.offer_id} does not exist.")
        self._attempts[key] = attempt
        return attempt

    def get_for_offer_version(
        self, offer_id: str, rule_version: int
    ) -> AutoAcceptAttempt | None:
        return self._attempts.get((offer_id, rule_version))

    def list_for_worker(self, worker_id: str, limit: int) -> list[AutoAcceptAttempt]:
        owned: list[AutoAcceptAttempt] = []
        for attempt in self._attempts.values():
            offer = self._offers.get(attempt.offer_id)
            if offer is None:
                raise RuntimeError(f"Attempt {attempt.attempt_id} has no offer.")
            if offer.worker_id == worker_id:
                owned.append(attempt)
        return sorted(owned, key=lambda attempt: attempt.evaluated_at, reverse=True)[:limit]

    def clear(self) -> None:
        self._attempts.clear()

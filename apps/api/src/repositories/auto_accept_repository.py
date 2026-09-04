from __future__ import annotations

from typing import Protocol

from apps.api.src.models.auto_accept import AutoAcceptAttempt, WorkerAutoAcceptRule


class DuplicateAutoAcceptAttemptError(Exception):
    pass


class WorkerAutoAcceptRuleRepository(Protocol):
    def save(self, rule: WorkerAutoAcceptRule) -> WorkerAutoAcceptRule: ...

    def get(self, worker_id: str, venue_id: str) -> WorkerAutoAcceptRule | None: ...

    def list_for_worker(self, worker_id: str) -> list[WorkerAutoAcceptRule]: ...

    def delete(self, worker_id: str, venue_id: str) -> bool: ...


class AutoAcceptAttemptRepository(Protocol):
    def save(self, attempt: AutoAcceptAttempt) -> AutoAcceptAttempt: ...

    def get_for_offer_version(
        self, offer_id: str, rule_version: int
    ) -> AutoAcceptAttempt | None: ...

    def list_for_worker(self, worker_id: str, limit: int) -> list[AutoAcceptAttempt]: ...

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Any

AUTO_ACCEPT_OUTCOMES = ("accepted", "skipped", "failed")


@dataclass(frozen=True)
class WorkerAutoAcceptRule:
    rule_id: str
    worker_id: str
    venue_id: str
    enabled: bool
    roles: list[str]
    minimum_rate: Decimal | None
    minimum_notice_hours: int | None
    version: int
    created_at: datetime
    updated_at: datetime

    def __post_init__(self) -> None:
        if self.version < 1:
            raise ValueError("An auto-accept rule version must be positive.")
        if self.minimum_rate is not None and self.minimum_rate < 0:
            raise ValueError("An auto-accept minimum rate cannot be negative.")
        if self.minimum_notice_hours is not None and self.minimum_notice_hours < 0:
            raise ValueError("Auto-accept notice hours cannot be negative.")


@dataclass(frozen=True)
class AutoAcceptAttempt:
    attempt_id: str
    offer_id: str
    rule_id: str | None
    rule_version: int
    rule_snapshot: dict[str, Any]
    evaluated_at: datetime
    outcome: str
    reason: str | None = None

    def __post_init__(self) -> None:
        if self.rule_version < 0:
            raise ValueError("An auto-accept attempt rule version cannot be negative.")
        if self.outcome not in AUTO_ACCEPT_OUTCOMES:
            raise ValueError(f"Unknown auto-accept outcome '{self.outcome}'.")

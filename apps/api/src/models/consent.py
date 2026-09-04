from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

CONSENT_ACTIONS = ("granted", "withdrawn", "objected", "acknowledged")

PURPOSE_TERMS = "terms"
PURPOSE_PRIVACY = "privacy"
PURPOSE_PROFILING = "profiling"


@dataclass(frozen=True)
class ConsentEvent:
    event_id: str
    user_id: str
    purpose: str
    action: str
    basis: str
    policy_version: str
    source: str
    occurred_at: datetime

    def __post_init__(self) -> None:
        if self.action not in CONSENT_ACTIONS:
            raise ValueError(f"Unknown consent action: {self.action}")

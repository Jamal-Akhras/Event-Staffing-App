from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


def normalize_certification_name(name: str) -> str:
    return " ".join(name.strip().lower().split())


@dataclass(frozen=True)
class WorkerCertification:
    certification_id: str
    worker_id: str
    name: str
    display_name: str
    expires_at: datetime
    created_at: datetime
    updated_at: datetime
    reference: str | None = None

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("A certification requires its normalized name.")
        if self.name != normalize_certification_name(self.name):
            raise ValueError("Certification names are stored normalized.")
        if not self.display_name.strip():
            raise ValueError("A certification requires a display name.")
        if self.expires_at.tzinfo is None:
            raise ValueError("Certification expiry requires a timezone-aware timestamp.")

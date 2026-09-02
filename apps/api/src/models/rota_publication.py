from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Any


@dataclass(frozen=True)
class RotaPublication:
    publication_id: str
    venue_id: str
    week_start: date
    revision: int
    published_at: datetime
    published_by_user_id: str
    assignments: list[dict[str, Any]] = field(default_factory=list)

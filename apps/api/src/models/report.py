from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class Report:
    report_id: str
    reporter_user_id: str
    reporter_role: str
    subject_type: str
    subject_id: str
    category: str
    description: str
    status: str
    resolution_notes: str | None
    created_at: datetime
    updated_at: datetime

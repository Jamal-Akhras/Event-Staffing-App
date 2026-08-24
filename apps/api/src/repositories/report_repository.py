from __future__ import annotations

from typing import Protocol

from apps.api.src.models.report import Report


class ReportRepository(Protocol):
    def get(self, report_id: str) -> Report | None: ...

    def save(self, report: Report) -> Report: ...

    def list_by_reporter(self, user_id: str, limit: int = 50) -> list[Report]: ...

    def list_by_status(self, status: str | None, limit: int = 100) -> list[Report]: ...

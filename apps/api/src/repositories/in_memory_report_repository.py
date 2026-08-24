from __future__ import annotations

from apps.api.src.models.report import Report


class InMemoryReportRepository:
    def __init__(self) -> None:
        self._items: dict[str, Report] = {}

    def get(self, report_id: str) -> Report | None:
        return self._items.get(report_id)

    def save(self, report: Report) -> Report:
        self._items[report.report_id] = report
        return report

    def list_by_reporter(self, user_id: str, limit: int = 50) -> list[Report]:
        items = [item for item in self._items.values() if item.reporter_user_id == user_id]
        return sorted(items, key=lambda item: item.created_at, reverse=True)[:limit]

    def list_by_status(self, status: str | None, limit: int = 100) -> list[Report]:
        items = [item for item in self._items.values() if status is None or item.status == status]
        return sorted(items, key=lambda item: item.created_at)[:limit]

    def clear(self) -> None:
        self._items.clear()

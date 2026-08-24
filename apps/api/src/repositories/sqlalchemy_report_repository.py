from __future__ import annotations

from sqlalchemy import desc
from sqlalchemy.orm import Session

from apps.api.src.db.trust_models import ReportModel
from apps.api.src.models.report import Report


class SqlAlchemyReportRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def get(self, report_id: str) -> Report | None:
        row = self._session.get(ReportModel, report_id)
        return _to_domain(row) if row is not None else None

    def save(self, report: Report) -> Report:
        row = self._session.get(ReportModel, report.report_id)
        if row is None:
            row = ReportModel(report_id=report.report_id)
            self._session.add(row)
        for name in report.__dataclass_fields__:
            if name != "report_id":
                setattr(row, name, getattr(report, name))
        self._session.flush()
        return report

    def list_by_reporter(self, user_id: str, limit: int = 50) -> list[Report]:
        rows = (
            self._session.query(ReportModel)
            .filter(ReportModel.reporter_user_id == user_id)
            .order_by(desc(ReportModel.created_at))
            .limit(limit)
            .all()
        )
        return [_to_domain(row) for row in rows]

    def list_by_status(self, status: str | None, limit: int = 100) -> list[Report]:
        query = self._session.query(ReportModel)
        if status:
            query = query.filter(ReportModel.status == status)
        rows = query.order_by(ReportModel.created_at).limit(limit).all()
        return [_to_domain(row) for row in rows]


def _to_domain(row: ReportModel) -> Report:
    return Report(**{name: getattr(row, name) for name in Report.__dataclass_fields__})

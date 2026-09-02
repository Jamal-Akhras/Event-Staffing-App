from __future__ import annotations

from sqlalchemy import and_, exists, extract, func, or_, select
from sqlalchemy.orm import Session

from apps.api.src.db.models import ApplicationModel, ShiftModel, WorkerFeedStateModel
from apps.api.src.db.tenancy_models import VenueModel
from apps.api.src.db.workforce_models import WorkerRelationshipModel
from apps.api.src.models.organisation import Venue
from apps.api.src.models.worker_feed_query import WorkerFeedItem, WorkerFeedQuery
from apps.api.src.repositories.sqlalchemy_organisation_repository import _venue
from apps.api.src.repositories.sqlalchemy_shift_repository import _to_domain


class SqlAlchemyWorkerFeedQueryRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def list_page(self, query: WorkerFeedQuery) -> list[WorkerFeedItem]:
        statement = (
            select(ShiftModel, VenueModel)
            .join(VenueModel, VenueModel.venue_id == ShiftModel.venue_id)
            .where(VenueModel.market_id == query.market_id)
            .where(ShiftModel.status == "open")
            .where(ShiftModel.start_time > query.now)
            .where(ShiftModel.workers_filled < ShiftModel.workers_needed)
            .where(~_passed_exists(query.worker_id))
            .where(~_application_exists(query.worker_id))
            .where(_reaches_worker(query.worker_id))
        )
        if query.search:
            pattern = f"%{_escape_search(query.search)}%"
            statement = statement.where(
                or_(
                    ShiftModel.role.ilike(pattern, escape="\\"),
                    ShiftModel.location.ilike(pattern, escape="\\"),
                    VenueModel.name.ilike(pattern, escape="\\"),
                )
            )
        if query.minimum_pay is not None:
            statement = statement.where(ShiftModel.pay_rate >= query.minimum_pay)
        if query.timing == "today":
            statement = statement.where(
                ShiftModel.start_time >= query.today_start,
                ShiftModel.start_time < query.today_end,
            )
        elif query.timing == "weekend":
            local_start = func.timezone(query.timezone, ShiftModel.start_time)
            statement = statement.where(extract("isodow", local_start).in_((6, 7)))
        if query.position:
            statement = statement.where(
                or_(
                    ShiftModel.start_time > query.position.start_time,
                    and_(
                        ShiftModel.start_time == query.position.start_time,
                        ShiftModel.shift_id > query.position.shift_id,
                    ),
                )
            )
        rows = self._session.execute(
            statement.order_by(ShiftModel.start_time, ShiftModel.shift_id).limit(query.limit + 1)
        ).all()
        return [WorkerFeedItem(shift=_to_domain(shift), venue=_venue(venue)) for shift, venue in rows]


def _passed_exists(worker_id: str):
    return exists(
        select(1).where(
            WorkerFeedStateModel.worker_id == worker_id,
            WorkerFeedStateModel.shift_id == ShiftModel.shift_id,
            WorkerFeedStateModel.action == "passed",
        )
    )


def _application_exists(worker_id: str):
    return exists(
        select(1).where(
            ApplicationModel.worker_id == worker_id,
            ApplicationModel.shift_id == ShiftModel.shift_id,
        )
    )


def _escape_search(value: str) -> str:
    return value.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


def _reaches_worker(worker_id: str):
    return or_(
        ShiftModel.origin == "market",
        and_(ShiftModel.origin == "assigned", ShiftModel.assigned_worker_id == worker_id),
        and_(ShiftModel.origin == "pool", _pool_member_exists(worker_id)),
    )


def _pool_member_exists(worker_id: str):
    return exists(
        select(1).where(
            WorkerRelationshipModel.venue_id == ShiftModel.venue_id,
            WorkerRelationshipModel.worker_id == worker_id,
            WorkerRelationshipModel.status.in_(("active", "invited")),
            WorkerRelationshipModel.relationship_type != "one_off",
        )
    )

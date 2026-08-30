from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query

from apps.api.src.auth import ActorContext, ActorRole, get_actor_context, require_role
from apps.api.src.datetime_utils import utc_now
from apps.api.src.deps import get_venue_analytics_service, get_venue_insights_service
from apps.api.src.helpers import _shift_view
from apps.api.src.schemas_analytics import (
    AnalyticsGapResponse,
    AnalyticsResponse,
    AnalyticsRoleResponse,
)
from apps.api.src.schemas_insights import (
    AttendanceResponse,
    DayCoverageResponse,
    PendingApplicationsResponse,
    RosterActivityResponse,
    TonightShiftResponse,
    TonightWorkerResponse,
    VenueOverviewResponse,
    WorkerActivityResponse,
)
from apps.api.src.services.venue_analytics_service import VenueAnalyticsService
from apps.api.src.services.venue_insights_service import VenueInsightsService, VenueOverview

router = APIRouter(tags=["insights"])

MAX_WINDOW_DAYS = 31


def _venue(actor: ActorContext) -> str:
    require_role(actor.role, {ActorRole.OPERATOR})
    if not actor.account_id:
        raise HTTPException(status_code=400, detail="Select a venue before requesting insights.")
    return actor.account_id


@router.get("/insights/overview", response_model=VenueOverviewResponse)
def venue_overview(
    window_start: datetime | None = Query(default=None),
    days: int = Query(default=7, ge=1, le=MAX_WINDOW_DAYS),
    service: VenueInsightsService = Depends(get_venue_insights_service),
    actor: ActorContext = Depends(get_actor_context),
) -> VenueOverviewResponse:
    account_id = _venue(actor)
    now = utc_now()
    overview = service.overview(account_id, window_start or _start_of_day(now), days, now)
    return _overview_view(overview)


@router.get("/insights/roster", response_model=RosterActivityResponse)
def roster_activity(
    service: VenueInsightsService = Depends(get_venue_insights_service),
    actor: ActorContext = Depends(get_actor_context),
) -> RosterActivityResponse:
    account_id = _venue(actor)
    return RosterActivityResponse(
        workers=[
            WorkerActivityResponse(
                worker_id=row.worker_id,
                completed=row.completed,
                last_worked=row.last_worked,
                recently_broken=row.recently_broken,
            )
            for row in service.roster_activity(account_id, utc_now())
        ]
    )


@router.get("/insights/analytics", response_model=AnalyticsResponse)
def venue_analytics(
    period: str = Query(default="month", pattern="^(week|month|quarter)$"),
    service: VenueAnalyticsService = Depends(get_venue_analytics_service),
    actor: ActorContext = Depends(get_actor_context),
) -> AnalyticsResponse:
    summary = service.summarise(_venue(actor), period, utc_now())
    return AnalyticsResponse(
        **{
            name: getattr(summary, name)
            for name in (
                "period", "window_start", "window_end", "seats_posted", "seats_filled",
                "fill_rate", "applications", "applications_per_seat", "hours_staffed",
                "average_pay_rate", "currency", "fill_rate_trend", "applications_trend",
                "hours_trend", "rate_trend",
            )
        },
        gaps=[AnalyticsGapResponse(**vars(gap)) for gap in summary.gaps],
        roles=[AnalyticsRoleResponse(role=role, seats=seats) for role, seats in summary.roles],
    )


def _start_of_day(now: datetime) -> datetime:
    return now.replace(hour=0, minute=0, second=0, microsecond=0)


def _overview_view(overview: VenueOverview) -> VenueOverviewResponse:
    attendance = overview.attendance
    return VenueOverviewResponse(
        window_start=overview.window_start,
        days=[
            DayCoverageResponse(day=day.day, total_shifts=day.total_shifts, open_seats=day.open_seats)
            for day in overview.days
        ],
        open_seats=overview.open_seats,
        pending_applications=PendingApplicationsResponse(
            count=overview.pending.count,
            oldest_created_at=overview.pending.oldest_created_at,
        ),
        attendance=AttendanceResponse(
            completed=attendance.completed,
            no_shows=attendance.no_shows,
            total=attendance.total,
            rate=round(attendance.completed / attendance.total * 100) if attendance.total else None,
        ),
        tonight=[
            TonightShiftResponse(
                shift=_shift_view(row.shift),
                workers=[
                    TonightWorkerResponse(
                        booking_id=booking.booking_id,
                        worker_id=booking.worker_id,
                        state=booking.state.value,
                        check_in_code=booking.check_in_code if booking.state.value == "confirmed" else None,
                    )
                    for booking in row.bookings
                ],
                missing=max(row.shift.workers_needed - len(row.bookings), 0),
            )
            for row in overview.tonight
        ],
    )

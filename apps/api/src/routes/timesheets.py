from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response

from apps.api.src.auth import ActorContext, ActorRole, get_actor_context, require_role
from apps.api.src.deps import (
    get_booking_lifecycle_service,
    get_charge_recorder,
    get_event_recorder,
    get_idempotency_service,
    get_relationship_service,
    get_timesheet_service,
)
from apps.api.src.helpers import _now_or
from apps.api.src.rate_limit import actor_or_ip, limiter
from apps.api.src.routes.approval_effects import record_approval_effects
from apps.api.src.routes.idempotency_support import IdempotencyKeyHeader, replayed
from apps.api.src.routes.service_errors import raise_service_error
from apps.api.src.schemas import BookingTransitionRequest
from apps.api.src.schemas_timesheets import (
    AttendanceRecordRequest,
    ChargeCorrectionRequest,
    ChargeCorrectionResponse,
    HoursAdjustRequest,
    TimesheetApprovalRow,
    TimesheetAdjustmentResponse,
    TimesheetApproveRequest,
    TimesheetApproveResponse,
    TimesheetDayResponse,
    TimesheetWeekResponse,
    TimesheetWorkerResponse,
)
from apps.api.src.services.booking_lifecycle_service import BookingLifecycleService
from apps.api.src.services.charge_recorder import ChargeRecorder
from apps.api.src.services.errors import NotFoundError, ServiceError, ValidationError
from apps.api.src.services.event_recorder import EventRecorder
from apps.api.src.services.idempotency import IdempotencyConflict, IdempotencyService
from apps.api.src.services.relationship_service import RelationshipService
from apps.api.src.services.timesheet_service import TimesheetService, TimesheetWeek
from packages.domain.src.booking_state import BookingState

router = APIRouter(tags=["timesheets"])


@router.get("/venues/me/timesheet", response_model=TimesheetWeekResponse)
def timesheet_week(
    week_start: date = Query(...),
    service: TimesheetService = Depends(get_timesheet_service),
    actor: ActorContext = Depends(get_actor_context),
) -> TimesheetWeekResponse:
    venue_id = _venue_of(actor)
    try:
        return _week_view(service.week_view(venue_id, week_start))
    except ServiceError as exc:
        raise_service_error(exc)


@router.get("/venues/me/timesheet.csv")
def timesheet_csv(
    week_start: date = Query(...),
    service: TimesheetService = Depends(get_timesheet_service),
    actor: ActorContext = Depends(get_actor_context),
) -> Response:
    venue_id = _venue_of(actor)
    try:
        body = service.csv_for_week(venue_id, week_start)
    except ServiceError as exc:
        raise_service_error(exc)
    return Response(
        content=body,
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="timesheet-{week_start}.csv"'},
    )


@router.post("/venues/me/timesheet/approve", response_model=TimesheetApproveResponse)
@limiter.limit("30/hour", key_func=actor_or_ip)
def approve_timesheet(
    request: Request,
    payload: TimesheetApproveRequest,
    response: Response,
    idempotency_key: IdempotencyKeyHeader = None,
    idempotency: IdempotencyService = Depends(get_idempotency_service),
    service: TimesheetService = Depends(get_timesheet_service),
    lifecycle: BookingLifecycleService = Depends(get_booking_lifecycle_service),
    charges: ChargeRecorder = Depends(get_charge_recorder),
    relationships: RelationshipService = Depends(get_relationship_service),
    actor: ActorContext = Depends(get_actor_context),
    recorder: EventRecorder = Depends(get_event_recorder),
) -> TimesheetApproveResponse:
    venue_id = _venue_of(actor)
    try:
        started = idempotency.start(
            actor.user_id, "timesheet.approve", idempotency_key, payload.model_dump(mode="json")
        )
    except IdempotencyConflict as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    if started.cached_response is not None:
        return replayed(response, TimesheetApproveResponse, started.cached_response)

    now = _now_or(payload.now)
    results: list[TimesheetApprovalRow] = []
    for booking_id in dict.fromkeys(payload.booking_ids):
        results.append(
            TimesheetApprovalRow(
                booking_id=booking_id,
                result=_approve_one(
                    service, lifecycle, charges, relationships, recorder, actor, venue_id, booking_id, now
                ),
            )
        )
    result = TimesheetApproveResponse(results=results)
    idempotency.finish(started.record_id, result.model_dump(mode="json"))
    return result


@router.post("/venues/me/timesheet/bookings/{booking_id}/adjust")
def adjust_hours(
    booking_id: str,
    payload: HoursAdjustRequest,
    service: TimesheetService = Depends(get_timesheet_service),
    actor: ActorContext = Depends(get_actor_context),
    recorder: EventRecorder = Depends(get_event_recorder),
) -> dict:
    venue_id = _venue_of(actor)
    try:
        booking = service.adjust_hours(
            venue_id, booking_id, payload.checked_in_at, payload.checked_out_at,
            payload.reason, actor.user_id, _now_or(payload.now),
        )
    except ServiceError as exc:
        raise_service_error(exc)
    recorder.record(
        "timesheet.hours_adjusted",
        "audit",
        actor=actor,
        subject_type="booking",
        subject_id=booking_id,
        worker_id=booking.worker_id,
        context={"reason": payload.reason},
    )
    return {"booking_id": booking_id, "status": "adjusted"}


@router.post("/venues/me/timesheet/bookings/{booking_id}/attendance")
def record_attendance(
    booking_id: str,
    payload: AttendanceRecordRequest,
    service: TimesheetService = Depends(get_timesheet_service),
    actor: ActorContext = Depends(get_actor_context),
    recorder: EventRecorder = Depends(get_event_recorder),
) -> dict:
    venue_id = _venue_of(actor)
    try:
        booking = service.record_attendance(
            venue_id, booking_id, payload.checked_in_at, payload.checked_out_at,
            actor.user_id, _now_or(payload.now),
        )
    except ServiceError as exc:
        raise_service_error(exc)
    recorder.record(
        "timesheet.attendance_recorded",
        "audit",
        actor=actor,
        subject_type="booking",
        subject_id=booking_id,
        worker_id=booking.worker_id,
        context={
            "checked_in_at": payload.checked_in_at.isoformat(),
            "checked_out_at": payload.checked_out_at.isoformat(),
        },
    )
    return {"booking_id": booking_id, "status": "recorded"}


@router.post("/venues/me/timesheet/charges/{charge_id}/correct", response_model=ChargeCorrectionResponse)
def correct_charge(
    charge_id: str,
    payload: ChargeCorrectionRequest,
    response: Response,
    idempotency_key: IdempotencyKeyHeader = None,
    idempotency: IdempotencyService = Depends(get_idempotency_service),
    service: TimesheetService = Depends(get_timesheet_service),
    actor: ActorContext = Depends(get_actor_context),
    recorder: EventRecorder = Depends(get_event_recorder),
) -> ChargeCorrectionResponse:
    venue_id = _venue_of(actor)
    try:
        started = idempotency.start(
            actor.user_id, "charge.correct", idempotency_key,
            {"charge_id": charge_id, **payload.model_dump(mode="json")},
        )
    except IdempotencyConflict as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    if started.cached_response is not None:
        return replayed(response, ChargeCorrectionResponse, started.cached_response)

    try:
        adjustment = service.correct_charge(
            venue_id, charge_id, payload.delta_hours, payload.reason, actor.user_id, _now_or(payload.now)
        )
    except ServiceError as exc:
        raise_service_error(exc)
    recorder.record(
        "billing.charge_corrected",
        "audit",
        actor=actor,
        subject_type="booking_charge",
        subject_id=charge_id,
        context={
            "adjustment_id": adjustment.adjustment_id,
            "delta_hours": str(adjustment.delta_hours),
            "delta_wages": str(adjustment.delta_wages),
            "delta_fee": str(adjustment.delta_fee),
        },
    )
    result = ChargeCorrectionResponse(
        adjustment_id=adjustment.adjustment_id,
        charge_id=adjustment.charge_id,
        booking_id=adjustment.booking_id,
        delta_hours=adjustment.delta_hours,
        delta_wages=adjustment.delta_wages,
        delta_fee=adjustment.delta_fee,
        reason=adjustment.reason,
        created_at=adjustment.created_at,
    )
    idempotency.finish(started.record_id, result.model_dump(mode="json"))
    return result


def _approve_one(
    service: TimesheetService,
    lifecycle: BookingLifecycleService,
    charges: ChargeRecorder,
    relationships: RelationshipService,
    recorder: EventRecorder,
    actor: ActorContext,
    venue_id: str,
    booking_id: str,
    now,
) -> str:
    try:
        booking = service._venue_booking(venue_id, booking_id)
    except NotFoundError:
        return "not_found"
    if booking.state in (BookingState.APPROVED, BookingState.PAID):
        return "already_approved"
    if booking.state != BookingState.CHECKED_OUT:
        return "not_approvable_state"
    if booking.attendance_mode != "employed":
        return "needs_worker_code"
    try:
        approved = lifecycle.transition(
            booking_id,
            BookingState.APPROVED,
            BookingTransitionRequest(now=now),
            actor.user_id,
            True,
            actor_role="operator",
        )
    except ValidationError:
        return "not_approvable_state"
    recorder.record(
        "booking.approved",
        "lifecycle",
        actor=actor,
        subject_type="booking",
        subject_id=booking_id,
        worker_id=approved.worker_id,
        context={"shift_id": approved.shift_id, "via": "timesheet"},
    )
    record_approval_effects(approved, actor, recorder, charges, relationships)
    return "approved"


def _venue_of(actor: ActorContext) -> str:
    require_role(actor.role, {ActorRole.OPERATOR})
    if not actor.account_id:
        raise HTTPException(status_code=403, detail="This account is not linked to a venue.")
    return actor.account_id


def _week_view(week: TimesheetWeek) -> TimesheetWeekResponse:
    return TimesheetWeekResponse(
        venue_id=week.venue_id,
        week_start=week.week_start,
        workers=[
            TimesheetWorkerResponse(
                worker_id=worker.worker_id,
                display_name=worker.display_name,
                relationship_type=worker.relationship_type,
                contracted_hours_per_week=worker.contracted_hours_per_week,
                scheduled_hours=worker.scheduled_hours,
                worked_hours=worker.worked_hours,
                approved_hours=worker.approved_hours,
                days=[
                    TimesheetDayResponse(
                        day=row.day,
                        booking_id=row.booking.booking_id,
                        charge_id=row.charge_id,
                        shift_id=row.booking.shift_id,
                        role=row.shift_role,
                        state=row.booking.state.value,
                        attendance_mode=row.booking.attendance_mode,
                        scheduled_start=row.booking.start_time,
                        scheduled_end=row.booking.end_time,
                        scheduled_hours=row.scheduled_hours,
                        worked_hours=row.worked,
                        hours_source=row.hours_source,
                        approved_hours=row.approved_hours,
                        approved_wages=row.approved_wages,
                        adjustments_total_hours=row.adjustments_total_hours,
                        adjustments=[
                            TimesheetAdjustmentResponse(
                                adjustment_id=adjustment.adjustment_id,
                                delta_hours=adjustment.delta_hours,
                                delta_wages=adjustment.delta_wages,
                                delta_fee=adjustment.delta_fee,
                                reason=adjustment.reason,
                                created_at=adjustment.created_at,
                            )
                            for adjustment in row.adjustments
                        ],
                    )
                    for row in worker.rows
                ],
            )
            for worker in week.workers
        ],
        total_scheduled_hours=week.total_scheduled_hours,
        total_worked_hours=week.total_worked_hours,
        total_approved_hours=week.total_approved_hours,
        total_approved_wages=week.total_approved_wages,
    )

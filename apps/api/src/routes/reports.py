from __future__ import annotations

from dataclasses import replace
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, Request

from apps.api.src.auth import ActorContext, ActorRole, get_actor_context, require_role, require_verified_actor
from apps.api.src.datetime_utils import utc_now
from apps.api.src.deps import (
    get_application_repo,
    get_booking_repo,
    get_message_repo,
    get_organisation_repo,
    get_report_repo,
    get_shift_repo,
)
from apps.api.src.models.report import Report
from apps.api.src.rate_limit import actor_or_ip, limiter
from apps.api.src.repositories.application_repository import ApplicationRepository
from apps.api.src.repositories.booking_repository import BookingRepository
from apps.api.src.repositories.message_repository import MessageRepository
from apps.api.src.repositories.organisation_repository import OrganisationRepository
from apps.api.src.repositories.report_repository import ReportRepository
from apps.api.src.repositories.shift_repository import ShiftRepository
from apps.api.src.routes.service_errors import raise_service_error
from apps.api.src.schemas_reports import ReportCreateRequest, ReportResponse, ReportReviewRequest
from apps.api.src.services.errors import ServiceError
from apps.api.src.services.report_access import require_report_subject_access

router = APIRouter(tags=["reports"])


@router.post("/reports", response_model=ReportResponse, status_code=201)
@limiter.limit("10/hour", key_func=actor_or_ip)
def create_report(
    request: Request,
    payload: ReportCreateRequest,
    actor: ActorContext = Depends(get_actor_context),
    repo: ReportRepository = Depends(get_report_repo),
    applications: ApplicationRepository = Depends(get_application_repo),
    bookings: BookingRepository = Depends(get_booking_repo),
    messages: MessageRepository = Depends(get_message_repo),
    organisations: OrganisationRepository = Depends(get_organisation_repo),
    shifts: ShiftRepository = Depends(get_shift_repo),
) -> ReportResponse:
    require_role(actor.role, {ActorRole.WORKER, ActorRole.OPERATOR})
    require_verified_actor(actor, "submitting reports")
    try:
        require_report_subject_access(
            actor,
            payload.subject_type,
            payload.subject_id,
            applications,
            bookings,
            messages,
            organisations,
            shifts,
        )
    except ServiceError as exc:
        raise_service_error(exc)
    now = utc_now()
    report = repo.save(
        Report(
            report_id=str(uuid4()),
            reporter_user_id=actor.user_id,
            reporter_role=actor.role.value,
            subject_type=payload.subject_type,
            subject_id=payload.subject_id,
            category=payload.category,
            description=payload.description,
            status="submitted",
            resolution_notes=None,
            created_at=now,
            updated_at=now,
        )
    )
    return ReportResponse(**report.__dict__)


@router.get("/reports/me", response_model=list[ReportResponse])
def list_my_reports(
    limit: int = Query(default=50, ge=1, le=100),
    actor: ActorContext = Depends(get_actor_context),
    repo: ReportRepository = Depends(get_report_repo),
) -> list[ReportResponse]:
    require_role(actor.role, {ActorRole.WORKER, ActorRole.OPERATOR})
    return [ReportResponse(**item.__dict__) for item in repo.list_by_reporter(actor.user_id, limit)]


@router.get("/system/reports", response_model=list[ReportResponse])
def list_reports_for_review(
    status: str | None = Query(default=None, pattern="^(submitted|reviewing|resolved|dismissed)$"),
    limit: int = Query(default=100, ge=1, le=100),
    actor: ActorContext = Depends(get_actor_context),
    repo: ReportRepository = Depends(get_report_repo),
) -> list[ReportResponse]:
    require_role(actor.role, {ActorRole.SYSTEM})
    return [ReportResponse(**item.__dict__) for item in repo.list_by_status(status, limit)]


@router.patch("/system/reports/{report_id}", response_model=ReportResponse)
def review_report(
    report_id: str,
    payload: ReportReviewRequest,
    actor: ActorContext = Depends(get_actor_context),
    repo: ReportRepository = Depends(get_report_repo),
) -> ReportResponse:
    require_role(actor.role, {ActorRole.SYSTEM})
    report = repo.get(report_id)
    if report is None:
        raise HTTPException(status_code=404, detail="Report not found.")
    updated = repo.save(
        replace(
            report,
            status=payload.status,
            resolution_notes=payload.resolution_notes,
            updated_at=utc_now(),
        )
    )
    return ReportResponse(**updated.__dict__)

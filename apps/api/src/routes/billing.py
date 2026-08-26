from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, Request

from apps.api.src.auth import ActorContext, ActorRole, get_actor_context, require_role
from apps.api.src.datetime_utils import utc_now
from apps.api.src.deps import get_billing_service
from apps.api.src.rate_limit import actor_or_ip, limiter
from apps.api.src.routes.service_errors import raise_service_error
from apps.api.src.schemas_billing import (
    BillingLineResponse,
    BillingSummaryResponse,
    RedeemPartnerCodeRequest,
    WaiverResponse,
)
from apps.api.src.services.billing_service import BillingService, BillingSummary, Waiver
from apps.api.src.services.errors import ServiceError

router = APIRouter(tags=["billing"])


@router.get("/billing/summary", response_model=BillingSummaryResponse)
def billing_summary(
    month: str | None = Query(default=None, pattern=r"^\d{4}-(0[1-9]|1[0-2])$"),
    actor: ActorContext = Depends(get_actor_context),
    service: BillingService = Depends(get_billing_service),
) -> BillingSummaryResponse:
    account_id = _venue_of(actor)
    now = utc_now()
    try:
        return _summary_view(service.summary(account_id, month or now.strftime("%Y-%m"), now))
    except ServiceError as exc:
        raise_service_error(exc)


@router.post("/billing/partner-codes/redeem", response_model=WaiverResponse)
@limiter.limit("10/hour", key_func=actor_or_ip)
def redeem_partner_code(
    request: Request,
    payload: RedeemPartnerCodeRequest,
    actor: ActorContext = Depends(get_actor_context),
    service: BillingService = Depends(get_billing_service),
) -> WaiverResponse:
    account_id = _venue_of(actor)
    try:
        waiver = service.redeem(payload.code, account_id, actor.user_id, utc_now())
    except ServiceError as exc:
        raise_service_error(exc)
    return _waiver_view(waiver)


def _venue_of(actor: ActorContext) -> str:
    require_role(actor.role, {ActorRole.OPERATOR})
    if not actor.account_id:
        raise HTTPException(status_code=403, detail="This account is not linked to a venue.")
    return actor.account_id


def _summary_view(summary: BillingSummary) -> BillingSummaryResponse:
    return BillingSummaryResponse(
        month=summary.month,
        fee_percent=summary.fee_percent,
        plan=summary.plan,
        waiver=_waiver_view(summary.waiver) if summary.waiver else None,
        lines=[BillingLineResponse(**line.__dict__) for line in summary.lines],
        wages_total=summary.wages_total,
        fee_total=summary.fee_total,
        grand_total=summary.grand_total,
        completed_shifts_all_time=summary.completed_shifts_all_time,
    )


def _waiver_view(waiver: Waiver) -> WaiverResponse:
    return WaiverResponse(
        code=waiver.code,
        label=waiver.label,
        fee_waived_until=waiver.fee_waived_until,
        shift_cap=waiver.shift_cap,
        shifts_used=waiver.shifts_used,
        active=waiver.active,
    )

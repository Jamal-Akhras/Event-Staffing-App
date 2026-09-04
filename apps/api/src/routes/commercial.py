from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from apps.api.src.auth import ActorContext, ActorRole, get_actor_context, require_role
from apps.api.src.auth.permissions import MANAGE_BILLING, require_permission
from apps.api.src.datetime_utils import utc_now
from apps.api.src.deps import get_commercial_service
from apps.api.src.routes.service_errors import raise_service_error
from apps.api.src.services.commercial_service import CommercialService
from apps.api.src.services.errors import ServiceError
from apps.api.src.validation_types import MoneyAmount, UtcTimestamp

router = APIRouter(tags=["commercial"])


class PlanResponse(BaseModel):
    plan: str
    monthly_fee_per_site: MoneyAmount
    own_pool_fee_percent: MoneyAmount
    outside_fee_percent: MoneyAmount
    currency: str
    effective_from: UtcTimestamp


class PlanChangeRequest(BaseModel):
    plan: Literal["classic", "plus"]


class BoostRequest(BaseModel):
    tier: Literal["top1", "top5", "top10"]


class BoostResponse(BaseModel):
    boost_id: str
    shift_id: str
    tier: str
    price: MoneyAmount
    currency: str
    status: str
    purchased_at: UtcTimestamp


@router.get("/organisations/me/plan", response_model=PlanResponse)
def get_plan(
    actor: ActorContext = Depends(get_actor_context),
    service: CommercialService = Depends(get_commercial_service),
) -> PlanResponse:
    organisation_id = _organisation_of(actor)
    require_permission(actor, MANAGE_BILLING)
    agreement = service.current_agreement(organisation_id, utc_now())
    return _plan_view(agreement)


@router.put("/organisations/me/plan", response_model=PlanResponse)
def change_plan(
    payload: PlanChangeRequest,
    actor: ActorContext = Depends(get_actor_context),
    service: CommercialService = Depends(get_commercial_service),
) -> PlanResponse:
    organisation_id = _organisation_of(actor)
    require_permission(actor, MANAGE_BILLING)
    try:
        agreement = service.change_plan(organisation_id, payload.plan, actor.user_id, utc_now())
    except ServiceError as exc:
        raise_service_error(exc)
    return _plan_view(agreement)


@router.post("/shifts/{shift_id}/boost", response_model=BoostResponse, status_code=201)
def buy_boost(
    shift_id: str,
    payload: BoostRequest,
    actor: ActorContext = Depends(get_actor_context),
    service: CommercialService = Depends(get_commercial_service),
) -> BoostResponse:
    require_role(actor.role, {ActorRole.OPERATOR})
    require_permission(actor, MANAGE_BILLING)
    if not actor.account_id:
        raise HTTPException(status_code=403, detail="This account is not linked to a venue.")
    try:
        boost = service.purchase_boost(
            shift_id, actor.account_id, payload.tier, actor.user_id, utc_now()
        )
    except ServiceError as exc:
        raise_service_error(exc)
    return BoostResponse(
        boost_id=boost.boost_id,
        shift_id=boost.shift_id,
        tier=boost.tier,
        price=boost.price,
        currency=boost.currency,
        status=boost.status,
        purchased_at=boost.purchased_at,
    )


def _organisation_of(actor: ActorContext) -> str:
    require_role(actor.role, {ActorRole.OPERATOR})
    if not actor.organisation_id:
        raise HTTPException(status_code=403, detail="This account has no organisation.")
    return actor.organisation_id


def _plan_view(agreement) -> PlanResponse:
    return PlanResponse(
        plan=agreement.plan,
        monthly_fee_per_site=agreement.monthly_fee_per_site,
        own_pool_fee_percent=agreement.own_pool_fee_percent,
        outside_fee_percent=agreement.outside_fee_percent,
        currency=agreement.currency,
        effective_from=agreement.effective_from,
    )

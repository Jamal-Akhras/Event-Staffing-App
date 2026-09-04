from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from apps.api.src.auth import ActorContext, ActorRole, get_actor_context, require_role
from apps.api.src.datetime_utils import utc_now
from apps.api.src.deps import get_insight_aggregates_service
from apps.api.src.services.insight_aggregates_service import (
    CoverageCost,
    FillFactors,
    InsightAggregatesService,
    PlanningValue,
    SavingsAvailable,
)
from apps.api.src.validation_types import MoneyAmount, UtcTimestamp

router = APIRouter(tags=["insights"])


class SourceCostResponse(BaseModel):
    source: str
    shifts: int
    hours: MoneyAmount
    wages: MoneyAmount
    fees: MoneyAmount
    cost_per_hour: MoneyAmount | None


class CoverageCostResponse(BaseModel):
    period: str
    sources: list[SourceCostResponse]
    hours: MoneyAmount
    wages: MoneyAmount
    fees: MoneyAmount
    cost_per_hour: MoneyAmount | None


class SavingOpportunityResponse(BaseModel):
    shift_id: str
    role: str
    start_time: UtcTimestamp
    available_candidates: int
    fee_avoided: MoneyAmount


class SavingsAvailableResponse(BaseModel):
    opportunities: list[SavingOpportunityResponse]
    total_fee_avoided: MoneyAmount


class FillBucketResponse(BaseModel):
    label: str
    shifts: int
    filled: int
    fill_rate: MoneyAmount | None


class FillFactorsResponse(BaseModel):
    lookback_days: int
    by_lead_time: list[FillBucketResponse]
    by_weekday: list[FillBucketResponse]
    by_pay_band: list[FillBucketResponse]


class PlanningBucketResponse(BaseModel):
    label: str
    shifts: int
    filled: int
    fill_rate: MoneyAmount | None
    average_escalation_depth: MoneyAmount | None


class PlanningValueResponse(BaseModel):
    lookback_days: int
    by_posting_lead: list[PlanningBucketResponse]


@router.get("/insights/cost-of-coverage", response_model=CoverageCostResponse)
def cost_of_coverage(
    month: str | None = Query(default=None, pattern=r"^\d{4}-\d{2}$"),
    actor: ActorContext = Depends(get_actor_context),
    service: InsightAggregatesService = Depends(get_insight_aggregates_service),
) -> CoverageCostResponse:
    venue_id = _venue(actor)
    period = month or utc_now().strftime("%Y-%m")
    return _coverage_view(service.cost_of_coverage(venue_id, period))


@router.get("/insights/savings-available", response_model=SavingsAvailableResponse)
def savings_available(
    actor: ActorContext = Depends(get_actor_context),
    service: InsightAggregatesService = Depends(get_insight_aggregates_service),
) -> SavingsAvailableResponse:
    venue_id = _venue(actor)
    result = service.savings_available(venue_id, utc_now())
    return _savings_view(result)


@router.get("/insights/what-helps-fill", response_model=FillFactorsResponse)
def what_helps_fill(
    actor: ActorContext = Depends(get_actor_context),
    service: InsightAggregatesService = Depends(get_insight_aggregates_service),
) -> FillFactorsResponse:
    venue_id = _venue(actor)
    return _fill_view(service.what_helps_fill(venue_id, utc_now()))


@router.get("/insights/value-of-planning", response_model=PlanningValueResponse)
def value_of_planning(
    actor: ActorContext = Depends(get_actor_context),
    service: InsightAggregatesService = Depends(get_insight_aggregates_service),
) -> PlanningValueResponse:
    venue_id = _venue(actor)
    return _planning_view(service.value_of_planning(venue_id, utc_now()))


def _venue(actor: ActorContext) -> str:
    require_role(actor.role, {ActorRole.OPERATOR})
    if not actor.account_id:
        raise HTTPException(status_code=403, detail="This account is not linked to a venue.")
    return actor.account_id


def _coverage_view(cost: CoverageCost) -> CoverageCostResponse:
    return CoverageCostResponse(
        period=cost.period,
        sources=[SourceCostResponse(**source.__dict__) for source in cost.sources],
        hours=cost.hours,
        wages=cost.wages,
        fees=cost.fees,
        cost_per_hour=cost.cost_per_hour,
    )


def _savings_view(result: SavingsAvailable) -> SavingsAvailableResponse:
    return SavingsAvailableResponse(
        opportunities=[
            SavingOpportunityResponse(**opportunity.__dict__)
            for opportunity in result.opportunities
        ],
        total_fee_avoided=result.total_fee_avoided,
    )


def _fill_view(factors: FillFactors) -> FillFactorsResponse:
    return FillFactorsResponse(
        lookback_days=factors.lookback_days,
        by_lead_time=[FillBucketResponse(**b.__dict__) for b in factors.by_lead_time],
        by_weekday=[FillBucketResponse(**b.__dict__) for b in factors.by_weekday],
        by_pay_band=[FillBucketResponse(**b.__dict__) for b in factors.by_pay_band],
    )


def _planning_view(value: PlanningValue) -> PlanningValueResponse:
    return PlanningValueResponse(
        lookback_days=value.lookback_days,
        by_posting_lead=[PlanningBucketResponse(**b.__dict__) for b in value.by_posting_lead],
    )

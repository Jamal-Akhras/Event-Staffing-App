from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from apps.api.src.auth import ActorContext, ActorRole, get_actor_context, require_role
from apps.api.src.datetime_utils import utc_now
from apps.api.src.deps import get_insight_aggregates_service
from apps.api.src.services.insight_aggregates_service import (
    CoverageCost,
    InsightAggregatesService,
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

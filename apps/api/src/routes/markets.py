from __future__ import annotations

from fastapi import APIRouter, Depends

from apps.api.src.deps import get_market_repo
from apps.api.src.repositories.market_repository import MarketRepository
from apps.api.src.schemas_market import MarketResponse

router = APIRouter(tags=["markets"])


@router.get("/markets", response_model=list[MarketResponse])
def list_markets(
    repo: MarketRepository = Depends(get_market_repo),
) -> list[MarketResponse]:
    return [MarketResponse.from_domain(market) for market in repo.list_active()]

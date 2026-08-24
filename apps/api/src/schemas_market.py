from __future__ import annotations

from dataclasses import asdict

from pydantic import BaseModel

from apps.api.src.models.organisation import Market
from apps.api.src.validation_types import MoneyAmount


class MarketResponse(BaseModel):
    market_id: str
    name: str
    country: str
    currency: str
    timezone: str
    high_pay_threshold: MoneyAmount

    @classmethod
    def from_domain(cls, market: Market) -> "MarketResponse":
        return cls(**asdict(market))

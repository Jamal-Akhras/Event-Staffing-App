from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

from apps.api.src.models.organisation import Market


class InMemoryMarketRepository:
    def __init__(self) -> None:
        bath = Market(
            market_id="bath-gb",
            name="Bath",
            country="GB",
            currency="GBP",
            timezone="Europe/London",
            high_pay_threshold=Decimal("15.00"),
            is_active=True,
            created_at=datetime(2026, 1, 1, tzinfo=UTC),
        )
        self._markets = {bath.market_id: bath}

    def get(self, market_id: str) -> Market | None:
        return self._markets.get(market_id)

    def list_active(self) -> list[Market]:
        return sorted(
            (market for market in self._markets.values() if market.is_active),
            key=lambda market: (market.name, market.market_id),
        )

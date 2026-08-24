from __future__ import annotations

from typing import Protocol

from apps.api.src.models.organisation import Market


class MarketRepository(Protocol):
    def get(self, market_id: str) -> Market | None:
        raise NotImplementedError

    def list_active(self) -> list[Market]:
        raise NotImplementedError

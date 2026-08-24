from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from apps.api.src.db.tenancy_models import MarketModel
from apps.api.src.money import money
from apps.api.src.models.organisation import Market


class SqlAlchemyMarketRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def get(self, market_id: str) -> Market | None:
        row = self._session.get(MarketModel, market_id)
        return _to_domain(row) if row else None

    def list_active(self) -> list[Market]:
        statement = (
            select(MarketModel)
            .where(MarketModel.is_active.is_(True))
            .order_by(MarketModel.name, MarketModel.market_id)
        )
        return [_to_domain(row) for row in self._session.scalars(statement)]


def _to_domain(row: MarketModel) -> Market:
    return Market(
        market_id=row.market_id,
        name=row.name,
        country=row.country,
        currency=row.currency,
        timezone=row.timezone,
        high_pay_threshold=money(row.high_pay_threshold),
        is_active=row.is_active,
        created_at=row.created_at,
    )

from __future__ import annotations

from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

from apps.api.src.repositories.account_repository import AccountRepository
from apps.api.src.repositories.market_repository import MarketRepository
from apps.api.src.services.errors import ValidationError


def venue_timezone(
    venue_id: str, accounts: AccountRepository, markets: MarketRepository
) -> ZoneInfo:
    venue = accounts.get(venue_id)
    if venue is None or venue.market_id is None:
        raise ValidationError("This venue has no market, so its local week cannot be resolved.")
    market = markets.get(venue.market_id)
    if market is None:
        raise ValidationError(f"Market {venue.market_id} was not found.")
    return ZoneInfo(market.timezone)


def week_window(week_start: date, zone: ZoneInfo) -> tuple[datetime, datetime]:
    start = datetime.combine(week_start, time.min, tzinfo=zone)
    end = datetime.combine(week_start + timedelta(days=7), time.min, tzinfo=zone)
    return start, end


def local_day(moment: datetime, zone: ZoneInfo) -> date:
    return moment.astimezone(zone).date()

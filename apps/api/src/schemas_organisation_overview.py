from __future__ import annotations

from decimal import Decimal

from pydantic import BaseModel

from apps.api.src.schemas_workforce import DirectoryEntryResponse
from apps.api.src.validation_types import MoneyAmount


class OrgStaffEntryResponse(BaseModel):
    venue_id: str
    venue_name: str
    person: DirectoryEntryResponse


class OrgVenueBillingResponse(BaseModel):
    venue_id: str
    venue_name: str
    wages_total: MoneyAmount
    fee_total: MoneyAmount
    amount_due: MoneyAmount


class OrgBillingSummaryResponse(BaseModel):
    month: str
    venues: list[OrgVenueBillingResponse]
    wages_total: MoneyAmount
    fee_total: MoneyAmount
    amount_due: MoneyAmount

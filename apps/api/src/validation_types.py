from __future__ import annotations

from decimal import Decimal
from typing import Annotated

from pydantic import AfterValidator, AwareDatetime, Field

from apps.api.src.datetime_utils import normalize_utc

MoneyAmount = Annotated[Decimal, Field(ge=0, max_digits=12, decimal_places=2)]
UtcTimestamp = Annotated[AwareDatetime, AfterValidator(normalize_utc)]

from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP

MONEY_PRECISION = 12
MONEY_SCALE = 2
MONEY_QUANTUM = Decimal("0.01")


def money(value: Decimal | float | int | str) -> Decimal:
    return Decimal(str(value)).quantize(MONEY_QUANTUM, rounding=ROUND_HALF_UP)

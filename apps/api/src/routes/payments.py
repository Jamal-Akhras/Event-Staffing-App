from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from apps.api.src.auth import ActorContext, ActorRole, get_actor_context, require_role
from apps.api.src.config import get_env

router = APIRouter(prefix="/payments", tags=["payments"])

MARKET_RATE_CARDS = {
    "GB": {
        "currency": "GBP",
        "provider": "stripe",
        "card_percent": Decimal("0.015"),
        "card_fixed": Decimal("0.20"),
        "bank_percent": Decimal("0.01"),
        "bank_fixed": Decimal("0.20"),
        "bank_cap": Decimal("4.00"),
    },
    "AE": {
        "currency": "AED",
        "provider": "stripe",
        "card_percent": Decimal("0.029"),
        "card_fixed": Decimal("1.00"),
        "bank_percent": Decimal("0"),
        "bank_fixed": Decimal("0"),
        "bank_cap": None,
    },
}


class PaymentQuoteRequest(BaseModel):
    country: str = Field(pattern="^(GB|AE)$")
    labor_total: float = Field(ge=0)
    method: str = Field(default="card", pattern="^(card|bank_transfer|manual)$")
    service_charge_rate: float | None = Field(default=None, ge=0, le=1)
    processing_fee_policy: str | None = Field(default=None, pattern="^(absorb|pass_through)$")


class PaymentQuoteResponse(BaseModel):
    country: str
    currency: str
    provider: str
    method: str
    labor_total: float
    service_charge_rate: float
    service_charge: float
    estimated_processing_fee: float
    platform_net_revenue: float
    venue_total: float
    processing_fee_policy: str
    live_mode: bool


@router.post("/quote", response_model=PaymentQuoteResponse)
def quote_payment(
    request: PaymentQuoteRequest,
    actor: ActorContext = Depends(get_actor_context),
) -> PaymentQuoteResponse:
    require_role(actor.role, {ActorRole.OPERATOR})
    rate_card = MARKET_RATE_CARDS[request.country]
    service_rate = _decimal_env("SERVICE_CHARGE_RATE", "0.10")
    if request.service_charge_rate is not None:
        service_rate = Decimal(str(request.service_charge_rate))
    fee_policy = request.processing_fee_policy or get_env("PROCESSING_FEE_POLICY", "pass_through")

    labor_total = _money(request.labor_total)
    service_charge = _round_money(labor_total * service_rate)
    subtotal = labor_total + service_charge
    processing_fee = _processing_fee(subtotal, request.method, fee_policy, rate_card)
    venue_total = subtotal + processing_fee if fee_policy == "pass_through" else subtotal
    platform_net = service_charge if fee_policy == "pass_through" else service_charge - processing_fee

    return PaymentQuoteResponse(
        country=request.country,
        currency=rate_card["currency"],
        provider=get_env("PAYMENT_PROVIDER", rate_card["provider"]),
        method=request.method,
        labor_total=float(labor_total),
        service_charge_rate=float(service_rate),
        service_charge=float(service_charge),
        estimated_processing_fee=float(processing_fee),
        platform_net_revenue=float(_round_money(platform_net)),
        venue_total=float(_round_money(venue_total)),
        processing_fee_policy=fee_policy,
        live_mode=get_env("PAYMENT_LIVE_MODE", "false").lower() == "true",
    )


def _processing_fee(subtotal: Decimal, method: str, fee_policy: str, rate_card: dict) -> Decimal:
    if method in {"manual", "bank_transfer"}:
        if method == "manual":
            return Decimal("0.00")
        return _capped_fee(subtotal, rate_card["bank_percent"], rate_card["bank_fixed"], rate_card["bank_cap"])

    percent = rate_card["card_percent"]
    fixed = rate_card["card_fixed"]
    if fee_policy == "pass_through":
        gross_total = (subtotal + fixed) / (Decimal("1") - percent)
        return _round_money(gross_total - subtotal)
    return _round_money((subtotal * percent) + fixed)


def _capped_fee(
    amount: Decimal,
    percent: Decimal,
    fixed: Decimal,
    cap: Decimal | None,
) -> Decimal:
    fee = _round_money((amount * percent) + fixed)
    if cap is not None and fee > cap:
        return cap
    return fee


def _decimal_env(name: str, default: str) -> Decimal:
    try:
        return Decimal(get_env(name, default))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Invalid {name}") from exc


def _money(value: float) -> Decimal:
    return _round_money(Decimal(str(value)))


def _round_money(value: Decimal) -> Decimal:
    return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

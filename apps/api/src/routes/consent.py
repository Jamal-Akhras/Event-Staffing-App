from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from apps.api.src.auth import ActorContext, get_actor_context
from apps.api.src.datetime_utils import utc_now
from apps.api.src.deps import get_consent_service
from apps.api.src.services.consent_service import ConsentService

router = APIRouter(tags=["consent"])


class ConsentStateResponse(BaseModel):
    consents: dict[str, str]


class ProfilingConsentRequest(BaseModel):
    granted: bool


@router.get("/me/consents", response_model=ConsentStateResponse)
def get_my_consents(
    actor: ActorContext = Depends(get_actor_context),
    service: ConsentService = Depends(get_consent_service),
) -> ConsentStateResponse:
    return ConsentStateResponse(consents=service.current_state(actor.user_id))


@router.put("/me/consents/profiling", response_model=ConsentStateResponse)
def set_profiling_consent(
    payload: ProfilingConsentRequest,
    actor: ActorContext = Depends(get_actor_context),
    service: ConsentService = Depends(get_consent_service),
) -> ConsentStateResponse:
    service.set_profiling(actor.user_id, payload.granted, utc_now())
    return ConsentStateResponse(consents=service.current_state(actor.user_id))

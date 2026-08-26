from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request

from apps.api.src.auth.schemas import SsoSignInRequest, TokenResponse
from apps.api.src.auth.session_tokens import issue_session, resolve_session_context
from apps.api.src.datetime_utils import utc_now
from apps.api.src.deps import get_organisation_repo
from apps.api.src.rate_limit import limiter
from apps.api.src.repositories.organisation_repository import OrganisationRepository
from apps.api.src.services.clerk_identity import IdentityVerificationError, IdentityVerifier
from apps.api.src.services.sso_service import (
    SsoAccountInactive,
    SsoEmailUnverified,
    SsoRegistrationRequired,
    SsoService,
)
from apps.api.src.sso_dependencies import get_identity_verifier, get_sso_service

router = APIRouter(prefix="/auth", tags=["auth"])

REGISTRATION_REQUIRED = "SSO_REGISTRATION_REQUIRED"


@router.post("/sso", response_model=TokenResponse)
@limiter.limit("10/minute")
def sign_in_with_sso(
    request: Request,
    payload: SsoSignInRequest,
    verifier: IdentityVerifier | None = Depends(get_identity_verifier),
    service: SsoService = Depends(get_sso_service),
    organisation_repo: OrganisationRepository = Depends(get_organisation_repo),
) -> TokenResponse:
    if verifier is None:
        raise HTTPException(status_code=503, detail="Single sign-on is not configured.")
    try:
        identity = verifier.verify(payload.token)
    except IdentityVerificationError as exc:
        raise HTTPException(status_code=401, detail=str(exc))
    try:
        user = service.sign_in(identity, payload.role, utc_now())
    except SsoRegistrationRequired as exc:
        raise HTTPException(status_code=404, detail={"code": REGISTRATION_REQUIRED, "email": exc.email})
    except SsoEmailUnverified:
        raise HTTPException(status_code=403, detail="Verify the email on your sign-in provider first.")
    except SsoAccountInactive:
        raise HTTPException(status_code=401, detail="Account is inactive")
    organisation_id, currency = resolve_session_context(user, organisation_repo)
    return issue_session(user, organisation_id=organisation_id, currency=currency)

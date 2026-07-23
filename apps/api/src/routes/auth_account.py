"""Account-lifecycle auth endpoints: logout (token revocation) and email verification."""

from __future__ import annotations

from dataclasses import replace
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from apps.api.src.auth.jwt import revoke_access_token
from apps.api.src.auth.schemas import (
    EmailVerificationResponse,
    LogoutResponse,
    ResendVerificationRequest,
    VerifyEmailRequest,
)
from apps.api.src.deps import get_user_repo
from apps.api.src.rate_limit import limiter
from apps.api.src.repositories.user_repository import UserRepository
from apps.api.src.services.email import get_email_transport
from apps.api.src.services.email_verification import (
    generate_verification_token,
    send_verification_email,
)

router = APIRouter(prefix="/auth", tags=["auth"])

_bearer = HTTPBearer(auto_error=False)


@router.post("/logout", response_model=LogoutResponse)
def logout(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
) -> LogoutResponse:
    if not credentials:
        raise HTTPException(status_code=401, detail="Authentication required")
    revoke_access_token(credentials.credentials)
    return LogoutResponse(message="Logged out. This token has been revoked.")


@router.post("/verify-email", response_model=EmailVerificationResponse)
def verify_email(
    payload: VerifyEmailRequest,
    user_repo: UserRepository = Depends(get_user_repo),
) -> EmailVerificationResponse:
    user = user_repo.get_by_verification_token(payload.token)
    if user is None:
        raise HTTPException(status_code=400, detail="Invalid or expired verification token.")
    verified = replace(
        user,
        email_verified=True,
        email_verification_token=None,
        updated_at=datetime.utcnow(),
    )
    user_repo.save(verified)
    return EmailVerificationResponse(message="Email verified.", email_verified=True)


@router.post("/resend-verification", response_model=EmailVerificationResponse)
@limiter.limit("5/hour")
def resend_verification(
    request: Request,
    payload: ResendVerificationRequest,
    user_repo: UserRepository = Depends(get_user_repo),
) -> EmailVerificationResponse:
    user = user_repo.get_by_email(payload.email)
    if user is None or user.email_verified:
        return EmailVerificationResponse(
            message="If that email needs verification, a new link has been sent.",
            email_verified=bool(user and user.email_verified),
        )
    token = generate_verification_token()
    updated = replace(
        user,
        email_verification_token=token,
        updated_at=datetime.utcnow(),
    )
    user_repo.save(updated)
    send_verification_email(get_email_transport(), updated.email, token)
    return EmailVerificationResponse(
        message="If that email needs verification, a new link has been sent.",
        email_verified=False,
    )

from __future__ import annotations

from dataclasses import replace

from fastapi import APIRouter, Depends, HTTPException, Request

from apps.api.src.auth.jwt import JWTError, create_reset_token, decode_reset_token
from apps.api.src.auth.password import hash_password
from apps.api.src.auth.schemas import (
    ForgotPasswordRequest,
    PasswordResetResponse,
    ResetPasswordRequest,
)
from apps.api.src.config import get_bool_env
from apps.api.src.datetime_utils import utc_now
from apps.api.src.deps import get_outbox_publisher, get_user_repo
from apps.api.src.rate_limit import limiter
from apps.api.src.repositories.user_repository import UserRepository
from apps.api.src.services.outbox_publisher import OutboxPublisher
from apps.api.src.services.password_reset_email import build_password_reset_email

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/forgot-password", response_model=PasswordResetResponse)
@limiter.limit("5/minute")
def forgot_password(
    request: Request,
    payload: ForgotPasswordRequest,
    user_repo: UserRepository = Depends(get_user_repo),
    outbox: OutboxPublisher = Depends(get_outbox_publisher),
) -> PasswordResetResponse:
    message = "If that email is registered, you'll receive a password reset link."
    user = user_repo.get_by_email(payload.email)
    if user is None:
        return PasswordResetResponse(message=message)
    token = create_reset_token(user.email)
    outbox.publish_email(
        event_type="auth.reset_password",
        aggregate_type="user",
        aggregate_id=user.user_id,
        email=build_password_reset_email(user.email, token),
        idempotency_suffix=token,
    )
    return PasswordResetResponse(
        message=message,
        reset_token=token if get_bool_env("DEV_MODE", False) else None,
    )


@router.post("/reset-password", response_model=PasswordResetResponse)
@limiter.limit("5/minute")
def reset_password(
    request: Request,
    payload: ResetPasswordRequest,
    user_repo: UserRepository = Depends(get_user_repo),
) -> PasswordResetResponse:
    try:
        claims = decode_reset_token(payload.token)
    except JWTError:
        raise HTTPException(status_code=400, detail="Invalid or expired reset token.")
    user = user_repo.get_by_email(claims.email)
    if user is None:
        raise HTTPException(status_code=400, detail="Invalid reset token.")
    if user.password_changed_at and claims.issued_at < user.password_changed_at:
        raise HTTPException(status_code=400, detail="Invalid or expired reset token.")
    now = utc_now()
    user_repo.save(
        replace(
            user,
            hashed_password=hash_password(payload.new_password),
            updated_at=now,
            password_changed_at=now,
            session_version=user.session_version + 1,
        )
    )
    return PasswordResetResponse(message="Password reset successfully. Please sign in.")

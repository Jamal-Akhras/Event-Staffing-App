from __future__ import annotations

from dataclasses import replace

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from apps.api.src.auth.dependencies import ActorContext, get_actor_context, get_current_user
from apps.api.src.auth.jwt import revoke_access_token
from apps.api.src.auth.password import verify_password
from apps.api.src.auth.schemas import (
    EmailVerificationResponse,
    LogoutResponse,
    ResendVerificationRequest,
    VerifyEmailRequest,
)
from apps.api.src.deps import get_outbox_publisher, get_user_repo
from apps.api.src.deps import get_request_session, get_worker_profile_repo
from apps.api.src.datetime_utils import utc_now
from apps.api.src.models.user import User
from apps.api.src.rate_limit import actor_or_ip, limiter
from apps.api.src.repositories.user_repository import UserRepository
from apps.api.src.repositories.worker_profile_repository import WorkerProfileRepository
from apps.api.src.repository_dependencies import get_request_unit_of_work
from apps.api.src.schemas_privacy import (
    AccountDeactivateRequest,
    AccountDeactivateResponse,
    AccountExportRequest,
    AccountExportResponse,
)
from apps.api.src.services.account_privacy import build_account_export, deactivate_account
from apps.api.src.services.email_verification import (
    build_verification_email,
    generate_verification_token,
)
from apps.api.src.services.outbox_publisher import OutboxPublisher
from apps.api.src.services.stored_upload import avatar_prefix, retire_objects_after_commit
from apps.api.src.storage.object_storage import ObjectStorage
from apps.api.src.storage_dependencies import get_object_storage
from apps.api.src.unit_of_work import RequestUnitOfWork

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


@router.post("/logout-all", response_model=LogoutResponse)
def logout_all(
    actor: ActorContext = Depends(get_actor_context),
    user_repo: UserRepository = Depends(get_user_repo),
) -> LogoutResponse:
    user = user_repo.get(actor.user_id)
    if user is None:
        raise HTTPException(status_code=401, detail="User not found or inactive")
    user_repo.save(
        replace(
            user,
            session_version=user.session_version + 1,
            updated_at=utc_now(),
        )
    )
    return LogoutResponse(message="Logged out on all devices.")


@router.post("/account-export", response_model=AccountExportResponse)
@limiter.limit("3/hour", key_func=actor_or_ip)
def export_account(
    request: Request,
    payload: AccountExportRequest,
    user: User = Depends(get_current_user),
    session: Session | None = Depends(get_request_session),
) -> AccountExportResponse:
    if not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=403, detail="Password confirmation failed.")
    if session is None:
        raise HTTPException(status_code=503, detail="Account export requires the database-backed API.")
    generated_at = utc_now()
    return AccountExportResponse(
        generated_at=generated_at,
        user_id=user.user_id,
        data=build_account_export(session, user, generated_at),
    )


@router.delete("/account", response_model=AccountDeactivateResponse)
@limiter.limit("3/hour", key_func=actor_or_ip)
def delete_account(
    request: Request,
    payload: AccountDeactivateRequest,
    user: User = Depends(get_current_user),
    user_repo: UserRepository = Depends(get_user_repo),
    worker_repo: WorkerProfileRepository = Depends(get_worker_profile_repo),
    session: Session | None = Depends(get_request_session),
    storage: ObjectStorage = Depends(get_object_storage),
    unit_of_work: RequestUnitOfWork = Depends(get_request_unit_of_work),
) -> AccountDeactivateResponse:
    if not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=403, detail="Password confirmation failed.")
    retired_avatar = deactivate_account(session, user_repo, worker_repo, user, utc_now())
    if retired_avatar and user.worker_profile_id:
        retire_objects_after_commit(
            storage,
            unit_of_work,
            {retired_avatar},
            avatar_prefix("workers", user.worker_profile_id),
        )
    return AccountDeactivateResponse(
        message="Account deactivated and personal profile data anonymized."
    )


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
        updated_at=utc_now(),
    )
    user_repo.save(verified)
    return EmailVerificationResponse(message="Email verified.", email_verified=True)


@router.post("/resend-verification", response_model=EmailVerificationResponse)
@limiter.limit("5/hour")
def resend_verification(
    request: Request,
    payload: ResendVerificationRequest,
    user_repo: UserRepository = Depends(get_user_repo),
    outbox: OutboxPublisher = Depends(get_outbox_publisher),
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
        updated_at=utc_now(),
    )
    user_repo.save(updated)
    outbox.publish_email(
        event_type="auth.verify_email",
        aggregate_type="user",
        aggregate_id=updated.user_id,
        email=build_verification_email(updated.email, token),
        idempotency_suffix=token,
    )
    return EmailVerificationResponse(
        message="If that email needs verification, a new link has been sent.",
        email_verified=False,
    )

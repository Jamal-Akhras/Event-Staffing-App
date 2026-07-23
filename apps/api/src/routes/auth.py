from __future__ import annotations

from dataclasses import replace
from datetime import datetime
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Request
from jose import JWTError

from apps.api.src.auth.dependencies import ActorContext, ActorRole, get_actor_context
from apps.api.src.auth.jwt import create_access_token, create_reset_token, decode_reset_token
from apps.api.src.auth.password import hash_password, verify_password
from apps.api.src.auth.schemas import (
    ForgotPasswordRequest,
    OperatorRegisterRequest,
    PasswordResetResponse,
    ResetPasswordRequest,
    SessionResponse,
    TokenResponse,
    UserLoginRequest,
    UserRegisterRequest,
)
from apps.api.src.config import get_bool_env
from apps.api.src.deps import get_account_repo, get_user_repo, get_worker_profile_repo
from apps.api.src.models.account import Account, COUNTRY_CURRENCY
from apps.api.src.models.user import User
from apps.api.src.models.worker_profile import WorkerProfile
from apps.api.src.rate_limit import limiter
from apps.api.src.repositories.account_repository import AccountRepository
from apps.api.src.repositories.user_repository import UserRepository
from apps.api.src.repositories.worker_profile_repository import WorkerProfileRepository
from apps.api.src.services.email import get_email_transport
from apps.api.src.services.email_verification import (
    generate_verification_token,
    send_verification_email,
)
from apps.api.src.services.operator_invites import is_valid_invite_code

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse)
@limiter.limit("10/hour")
def register(
    request: Request,
    payload: UserRegisterRequest,
    user_repo: UserRepository = Depends(get_user_repo),
    worker_repo: WorkerProfileRepository = Depends(get_worker_profile_repo),
) -> TokenResponse:
    existing = user_repo.get_by_email(payload.email)
    if existing is not None:
        raise HTTPException(status_code=400, detail="Email already registered")

    now = datetime.utcnow()
    user_id = str(uuid4())
    worker_profile_id = str(uuid4())
    verification_token = generate_verification_token()

    user = User(
        user_id=user_id,
        email=payload.email,
        hashed_password=hash_password(payload.password),
        role="worker",
        account_id=None,
        worker_profile_id=worker_profile_id,
        is_active=True,
        created_at=now,
        updated_at=now,
        email_verified=False,
        email_verification_token=verification_token,
    )
    user_repo.save(user)
    send_verification_email(get_email_transport(), user.email, verification_token)

    profile = WorkerProfile(
        worker_id=worker_profile_id,
        display_name="",
        role="",
        city="",
        experience_years=0,
        reliability_score=0.0,
        badges=[],
        bio=None,
        languages=[],
        email=payload.email,
        phone=None,
        address=None,
        emergency_contact=None,
        pay_rate=None,
        notes=None,
        updated_at=now,
    )
    worker_repo.save(profile)

    token = create_access_token(
        {"user_id": user_id, "email": user.email, "role": user.role, "account_id": None}
    )
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        user_id=user.user_id,
        email=user.email,
        role=user.role,
        account_id=None,
        worker_profile_id=worker_profile_id,
        currency="GBP",
        email_verified=user.email_verified,
    )


@router.post("/register/operator", response_model=TokenResponse)
@limiter.limit("10/hour")
def register_operator(
    request: Request,
    payload: OperatorRegisterRequest,
    user_repo: UserRepository = Depends(get_user_repo),
    account_repo: AccountRepository = Depends(get_account_repo),
) -> TokenResponse:
    if not is_valid_invite_code(payload.invite_code):
        raise HTTPException(status_code=403, detail="A valid operator invite code is required.")

    if payload.country not in COUNTRY_CURRENCY:
        raise HTTPException(status_code=400, detail=f"Unsupported country: {payload.country}. Must be GB or AE.")

    existing = user_repo.get_by_email(payload.email)
    if existing is not None:
        raise HTTPException(status_code=400, detail="Email already registered")

    now = datetime.utcnow()
    account_id = str(uuid4())
    verification_token = generate_verification_token()
    account = Account(
        account_id=account_id,
        name=payload.venue_name,
        country=payload.country,
        currency=COUNTRY_CURRENCY[payload.country],
        created_at=now,
    )
    account_repo.save(account)

    user = User(
        user_id=str(uuid4()),
        email=payload.email,
        hashed_password=hash_password(payload.password),
        role="operator",
        account_id=account_id,
        worker_profile_id=None,
        is_active=True,
        created_at=now,
        updated_at=now,
        email_verified=False,
        email_verification_token=verification_token,
    )
    user_repo.save(user)
    send_verification_email(get_email_transport(), user.email, verification_token)

    token = create_access_token(
        {"user_id": user.user_id, "email": user.email, "role": user.role, "account_id": account_id}
    )
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        user_id=user.user_id,
        email=payload.email,
        role=user.role,
        account_id=account_id,
        worker_profile_id=None,
        currency=account.currency,
        email_verified=user.email_verified,
    )


@router.post("/login", response_model=TokenResponse)
@limiter.limit("5/minute")
def login(
    request: Request,
    credentials: UserLoginRequest,
    user_repo: UserRepository = Depends(get_user_repo),
    account_repo: AccountRepository = Depends(get_account_repo),
) -> TokenResponse:
    user = user_repo.get_by_email(credentials.email)
    if user is None or not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    if not user.is_active:
        raise HTTPException(status_code=401, detail="Account is inactive")

    currency = "GBP"
    if user.account_id:
        account = account_repo.get(user.account_id)
        if account:
            currency = account.currency

    token = create_access_token(
        {"user_id": user.user_id, "email": user.email, "role": user.role, "account_id": user.account_id}
    )
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        user_id=user.user_id,
        email=user.email,
        role=user.role,
        account_id=user.account_id,
        worker_profile_id=user.worker_profile_id,
        currency=currency,
        email_verified=user.email_verified,
    )


@router.get("/me", response_model=SessionResponse)
def me(actor: ActorContext = Depends(get_actor_context)) -> SessionResponse:
    return SessionResponse(
        user_id=actor.user_id,
        role=actor.role.value,
        tenant_id=actor.account_id,
        auth_mode="dev_headers" if get_bool_env("DEV_MODE", False) else "jwt",
        data_scope="account_id",
    )


@router.post("/forgot-password", response_model=PasswordResetResponse)
@limiter.limit("5/minute")
def forgot_password(
    request: Request,
    payload: ForgotPasswordRequest,
    user_repo: UserRepository = Depends(get_user_repo),
) -> PasswordResetResponse:
    user = user_repo.get_by_email(payload.email)
    if user is None:
        return PasswordResetResponse(message="If that email is registered, you'll receive a reset token.")
    token = create_reset_token(user.email)
    dev_mode = get_bool_env("DEV_MODE", False)
    return PasswordResetResponse(
        message="Reset token generated. In production this is sent via email.",
        reset_token=token if dev_mode else None,
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
    now = datetime.utcnow()
    updated = replace(
        user,
        hashed_password=hash_password(payload.new_password),
        updated_at=now,
        password_changed_at=now,
    )
    user_repo.save(updated)
    return PasswordResetResponse(message="Password reset successfully. Please sign in.")

from __future__ import annotations

from uuid import uuid4
from fastapi import APIRouter, Depends, HTTPException, Request

from apps.api.src.auth.dependencies import ActorContext, ActorRole, get_actor_context
from apps.api.src.auth.jwt import create_access_token
from apps.api.src.auth.password import hash_password, verify_password
from apps.api.src.auth.schemas import (
    OperatorRegisterRequest,
    SessionResponse,
    TokenResponse,
    UserLoginRequest,
    UserRegisterRequest,
)
from apps.api.src.config import get_bool_env
from apps.api.src.datetime_utils import utc_now
from apps.api.src.deps import (
    get_account_repo,
    get_market_repo,
    get_organisation_repo,
    get_outbox_publisher,
    get_user_repo,
    get_worker_profile_repo,
)
from apps.api.src.models.organisation import (
    Organisation,
    OrganisationMembership,
    OrganisationRole,
    Venue,
)
from apps.api.src.models.user import User
from apps.api.src.models.worker_profile import WorkerProfile
from apps.api.src.rate_limit import limiter
from apps.api.src.repositories.account_repository import AccountRepository
from apps.api.src.repositories.market_repository import MarketRepository
from apps.api.src.repositories.organisation_repository import OrganisationRepository
from apps.api.src.repositories.user_repository import UserRepository
from apps.api.src.repositories.worker_profile_repository import WorkerProfileRepository
from apps.api.src.services.email_verification import (
    build_verification_email,
    generate_verification_token,
)
from apps.api.src.services.outbox_publisher import OutboxPublisher
from apps.api.src.services.operator_invites import is_valid_invite_code

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/register", response_model=TokenResponse)
@limiter.limit("10/hour")
def register(
    request: Request,
    payload: UserRegisterRequest,
    user_repo: UserRepository = Depends(get_user_repo),
    worker_repo: WorkerProfileRepository = Depends(get_worker_profile_repo),
    outbox: OutboxPublisher = Depends(get_outbox_publisher),
) -> TokenResponse:
    existing = user_repo.get_by_email(payload.email)
    if existing is not None:
        raise HTTPException(status_code=400, detail="Email already registered")

    now = utc_now()
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
    outbox.publish_email(
        event_type="auth.verify_email",
        aggregate_type="user",
        aggregate_id=user.user_id,
        email=build_verification_email(user.email, verification_token),
        idempotency_suffix=verification_token,
    )

    token = create_access_token(
        {
            "user_id": user_id,
            "email": user.email,
            "role": user.role,
            "account_id": None,
            "session_version": user.session_version,
        }
    )
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        user_id=user.user_id,
        email=user.email,
        role=user.role,
        account_id=None,
        organisation_id=None,
        venue_id=None,
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
    organisation_repo: OrganisationRepository = Depends(get_organisation_repo),
    market_repo: MarketRepository = Depends(get_market_repo),
    outbox: OutboxPublisher = Depends(get_outbox_publisher),
) -> TokenResponse:
    if not is_valid_invite_code(payload.invite_code):
        raise HTTPException(status_code=403, detail="A valid operator invite code is required.")

    market = market_repo.get(payload.market_id)
    if market is None or not market.is_active:
        raise HTTPException(status_code=400, detail="Invalid or inactive market.")
    if market.country != payload.country:
        raise HTTPException(status_code=400, detail="Market does not belong to the selected country.")

    existing = user_repo.get_by_email(payload.email)
    if existing is not None:
        raise HTTPException(status_code=400, detail="Email already registered")

    now = utc_now()
    organisation_id = str(uuid4())
    venue_id = str(uuid4())
    user_id = str(uuid4())
    verification_token = generate_verification_token()
    organisation = Organisation(
        organisation_id=organisation_id,
        name=payload.organisation_name or payload.venue_name,
        country=payload.country,
        currency=market.currency,
        created_at=now,
    )
    organisation_repo.save_organisation(organisation)
    venue = Venue(
        venue_id=venue_id,
        organisation_id=organisation_id,
        name=payload.venue_name,
        country=payload.country,
        currency=organisation.currency,
        created_at=now,
        market_id=market.market_id,
    )
    organisation_repo.save_venue(venue)

    user = User(
        user_id=user_id,
        email=payload.email,
        hashed_password=hash_password(payload.password),
        role="operator",
        account_id=venue_id,
        worker_profile_id=None,
        is_active=True,
        created_at=now,
        updated_at=now,
        email_verified=False,
        email_verification_token=verification_token,
    )
    user_repo.save(user)
    organisation_repo.save_membership(
        OrganisationMembership(
            organisation_id=organisation_id,
            user_id=user_id,
            role=OrganisationRole.OWNER,
            created_at=now,
        )
    )
    outbox.publish_email(
        event_type="auth.verify_email",
        aggregate_type="user",
        aggregate_id=user.user_id,
        email=build_verification_email(user.email, verification_token),
        idempotency_suffix=verification_token,
    )

    token = create_access_token(
        {
            "user_id": user.user_id,
            "email": user.email,
            "role": user.role,
            "account_id": venue_id,
            "venue_id": venue_id,
            "organisation_id": organisation_id,
            "session_version": user.session_version,
        }
    )
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        user_id=user.user_id,
        email=payload.email,
        role=user.role,
        account_id=venue_id,
        organisation_id=organisation_id,
        venue_id=venue_id,
        worker_profile_id=None,
        currency=venue.currency,
        email_verified=user.email_verified,
    )


@router.post("/login", response_model=TokenResponse)
@limiter.limit("5/minute")
def login(
    request: Request,
    credentials: UserLoginRequest,
    user_repo: UserRepository = Depends(get_user_repo),
    account_repo: AccountRepository = Depends(get_account_repo),
    organisation_repo: OrganisationRepository = Depends(get_organisation_repo),
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

    organisation_id = None
    if user.account_id:
        venue = organisation_repo.get_venue(user.account_id)
        if venue:
            organisation_id = venue.organisation_id

    token = create_access_token(
        {
            "user_id": user.user_id,
            "email": user.email,
            "role": user.role,
            "account_id": user.account_id,
            "venue_id": user.account_id,
            "organisation_id": organisation_id,
            "session_version": user.session_version,
        }
    )
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        user_id=user.user_id,
        email=user.email,
        role=user.role,
        account_id=user.account_id,
        organisation_id=organisation_id,
        venue_id=user.account_id,
        worker_profile_id=user.worker_profile_id,
        currency=currency,
        email_verified=user.email_verified,
    )


@router.get("/me", response_model=SessionResponse)
def me(actor: ActorContext = Depends(get_actor_context)) -> SessionResponse:
    return SessionResponse(
        user_id=actor.user_id,
        role=actor.role.value,
        tenant_id=actor.organisation_id,
        organisation_id=actor.organisation_id,
        venue_id=actor.account_id,
        auth_mode="dev_headers" if get_bool_env("DEV_MODE", False) else "jwt",
        data_scope="venue_id",
    )

from __future__ import annotations

from uuid import uuid4
from fastapi import APIRouter, Depends, HTTPException, Request

from apps.api.src.auth.dependencies import ActorContext, get_actor_context
from apps.api.src.auth.password import hash_password, verify_password
from apps.api.src.auth.schemas import (
    OperatorRegisterRequest,
    SessionResponse,
    TokenResponse,
    UserLoginRequest,
    UserRegisterRequest,
)
from apps.api.src.services.durable_events import record_durable
from apps.api.src.services.event_recorder import EventRecorder
from apps.api.src.auth.session_tokens import issue_session, resolve_session_context
from apps.api.src.config import get_bool_env
from apps.api.src.datetime_utils import utc_now
from apps.api.src.deps import (
    get_consent_service,
    get_event_recorder,
    get_join_code_service,
    get_market_repo,
    get_organisation_repo,
    get_outbox_publisher,
    get_user_repo,
    get_worker_profile_repo,
)
from apps.api.src.routes.service_errors import raise_service_error
from apps.api.src.services.errors import ServiceError
from apps.api.src.services.consent_service import ConsentService
from apps.api.src.services.join_code_service import JoinCodeService
from apps.api.src.models.organisation import (
    Organisation,
    OrganisationMembership,
    OrganisationRole,
    Venue,
)
from apps.api.src.models.user import User
from apps.api.src.models.worker_profile import WorkerProfile
from apps.api.src.rate_limit import limiter
from apps.api.src.repositories.market_repository import MarketRepository
from apps.api.src.repositories.organisation_repository import OrganisationRepository
from apps.api.src.repositories.user_repository import UserRepository
from apps.api.src.repositories.worker_profile_repository import WorkerProfileRepository
from apps.api.src.services.clerk_identity import IdentityVerificationError, IdentityVerifier, SsoIdentity
from apps.api.src.services.email_verification import (
    build_verification_email,
    generate_verification_token,
)
from apps.api.src.services.outbox_publisher import OutboxPublisher
from apps.api.src.services.operator_invites import is_valid_invite_code
from apps.api.src.services.sso_service import unusable_password_hash
from apps.api.src.sso_dependencies import get_identity_verifier

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse)
@limiter.limit("10/hour")
def register(
    request: Request,
    payload: UserRegisterRequest,
    user_repo: UserRepository = Depends(get_user_repo),
    worker_repo: WorkerProfileRepository = Depends(get_worker_profile_repo),
    outbox: OutboxPublisher = Depends(get_outbox_publisher),
    join_codes: JoinCodeService = Depends(get_join_code_service),
    consent_service: ConsentService = Depends(get_consent_service),
) -> TokenResponse:
    if user_repo.get_by_email(payload.email) is not None:
        raise HTTPException(status_code=400, detail="Email already registered")

    now = utc_now()
    if payload.join_code is not None:
        try:
            join_codes.preview(payload.join_code, now)
        except ServiceError as exc:
            raise_service_error(exc)
    worker_profile_id = str(uuid4())
    verification_token = generate_verification_token()
    user = User(
        user_id=str(uuid4()),
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
    consent_service.record_registration(user.user_id, now)
    worker_repo.save(
        WorkerProfile(
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
            marketplace_enabled=payload.join_code is None,
        )
    )
    if payload.join_code is not None:
        try:
            join_codes.redeem(payload.join_code, worker_profile_id, now)
        except ServiceError as exc:
            raise_service_error(exc)
    _send_verification(outbox, user, verification_token)
    return issue_session(user, organisation_id=None, currency="GBP")


@router.post("/register/operator", response_model=TokenResponse)
@limiter.limit("10/hour")
def register_operator(
    request: Request,
    payload: OperatorRegisterRequest,
    user_repo: UserRepository = Depends(get_user_repo),
    organisation_repo: OrganisationRepository = Depends(get_organisation_repo),
    market_repo: MarketRepository = Depends(get_market_repo),
    outbox: OutboxPublisher = Depends(get_outbox_publisher),
    verifier: IdentityVerifier | None = Depends(get_identity_verifier),
) -> TokenResponse:
    if not is_valid_invite_code(payload.invite_code):
        raise HTTPException(status_code=403, detail="A valid operator invite code is required.")

    market = market_repo.get(payload.market_id)
    if market is None or not market.is_active:
        raise HTTPException(status_code=400, detail="Invalid or inactive market.")
    if market.country != payload.country:
        raise HTTPException(status_code=400, detail="Market does not belong to the selected country.")

    identity = _verify_registration_identity(payload, verifier)
    email = identity.email if identity else payload.email
    if user_repo.get_by_email(email) is not None:
        raise HTTPException(status_code=400, detail="Email already registered")

    now = utc_now()
    organisation_id = str(uuid4())
    venue_id = str(uuid4())
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

    verification_token = None if identity else generate_verification_token()
    user = User(
        user_id=str(uuid4()),
        email=email,
        hashed_password=unusable_password_hash() if identity else hash_password(payload.password or ""),
        role="operator",
        account_id=venue_id,
        worker_profile_id=None,
        is_active=True,
        created_at=now,
        updated_at=now,
        email_verified=identity is not None,
        email_verification_token=verification_token,
        sso_provider=identity.provider if identity else None,
        sso_subject=identity.subject if identity else None,
    )
    user_repo.save(user)
    organisation_repo.save_membership(
        OrganisationMembership(
            organisation_id=organisation_id,
            user_id=user.user_id,
            role=OrganisationRole.OWNER,
            created_at=now,
        )
    )
    if verification_token:
        _send_verification(outbox, user, verification_token)
    return issue_session(user, organisation_id=organisation_id, currency=venue.currency)


@router.post("/login", response_model=TokenResponse)
@limiter.limit("5/minute")
def login(
    request: Request,
    credentials: UserLoginRequest,
    user_repo: UserRepository = Depends(get_user_repo),
    organisation_repo: OrganisationRepository = Depends(get_organisation_repo),
    recorder: EventRecorder = Depends(get_event_recorder),
) -> TokenResponse:
    user = user_repo.get_by_email(credentials.email)
    if user is None or not verify_password(credentials.password, user.hashed_password):
        record_durable("auth.login_failed", "auth", subject_type="email", context={"reason": "invalid_credentials"})
        raise HTTPException(status_code=401, detail="Invalid email or password")
    if not user.is_active:
        record_durable(
            "auth.login_failed",
            "auth",
            actor_user_id=user.user_id,
            subject_type="user",
            subject_id=user.user_id,
            context={"reason": "inactive"},
        )
        raise HTTPException(status_code=401, detail="Account is inactive")
    organisation_id, currency = resolve_session_context(user, organisation_repo)
    recorder.record(
        "auth.login",
        "auth",
        actor_user_id=user.user_id,
        actor_role=user.role,
        organisation_id=organisation_id,
        venue_id=user.account_id,
        subject_type="user",
        subject_id=user.user_id,
    )
    return issue_session(user, organisation_id=organisation_id, currency=currency)


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


def _verify_registration_identity(
    payload: OperatorRegisterRequest,
    verifier: IdentityVerifier | None,
) -> SsoIdentity | None:
    if payload.sso_token is None:
        return None
    if verifier is None:
        raise HTTPException(status_code=503, detail="Single sign-on is not configured.")
    try:
        identity = verifier.verify(payload.sso_token)
    except IdentityVerificationError as exc:
        raise HTTPException(status_code=401, detail=str(exc))
    if not identity.email_verified:
        raise HTTPException(status_code=403, detail="Verify the email on your sign-in provider first.")
    if identity.email != payload.email.lower():
        raise HTTPException(status_code=400, detail="The email does not match the signed-in account.")
    return identity


def _send_verification(outbox: OutboxPublisher, user: User, verification_token: str) -> None:
    outbox.publish_email(
        event_type="auth.verify_email",
        aggregate_type="user",
        aggregate_id=user.user_id,
        email=build_verification_email(user.email, verification_token),
        idempotency_suffix=verification_token,
    )

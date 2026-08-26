from __future__ import annotations

from apps.api.src.auth.jwt import create_access_token
from apps.api.src.auth.schemas import TokenResponse
from apps.api.src.models.user import User
from apps.api.src.repositories.organisation_repository import OrganisationRepository


def resolve_session_context(user: User, organisation_repo: OrganisationRepository) -> tuple[str | None, str]:
    venue = organisation_repo.get_venue(user.account_id) if user.account_id else None
    if venue is None:
        return None, "GBP"
    return venue.organisation_id, venue.currency


def issue_session(user: User, *, organisation_id: str | None, currency: str) -> TokenResponse:
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

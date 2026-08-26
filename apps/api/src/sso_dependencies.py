from __future__ import annotations

from functools import lru_cache

from fastapi import Depends

from apps.api.src.deps import get_user_repo, get_worker_profile_repo
from apps.api.src.repositories.user_repository import UserRepository
from apps.api.src.repositories.worker_profile_repository import WorkerProfileRepository
from apps.api.src.services.clerk_identity import ClerkIdentityVerifier, IdentityVerifier, get_clerk_settings
from apps.api.src.services.sso_service import SsoService


@lru_cache(maxsize=1)
def get_identity_verifier() -> IdentityVerifier | None:
    settings = get_clerk_settings()
    return ClerkIdentityVerifier(settings) if settings else None


def get_sso_service(
    user_repo: UserRepository = Depends(get_user_repo),
    worker_repo: WorkerProfileRepository = Depends(get_worker_profile_repo),
) -> SsoService:
    return SsoService(user_repo, worker_repo)

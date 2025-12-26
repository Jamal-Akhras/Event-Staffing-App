"""FastAPI dependencies for authentication."""

from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from apps.api.src.auth.jwt import decode_access_token
from apps.api.src.models.user import User
from apps.api.src.repositories.user_repository import UserRepository
from apps.api.src.deps import get_user_repo

security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    user_repo: UserRepository = Depends(get_user_repo),
) -> User:
    """Dependency that validates JWT and returns the current authenticated user.

    Args:
        credentials: HTTP Bearer credentials from the Authorization header
        user_repo: User repository for database access

    Returns:
        User object if authentication is successful

    Raises:
        HTTPException: 401 if token is invalid, expired, or user not found
    """
    token = credentials.credentials
    try:
        payload = decode_access_token(token)
        user_id = payload.get("user_id")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token payload")
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    user = user_repo.get(user_id)
    if user is None or not user.is_active:
        raise HTTPException(status_code=401, detail="User not found or inactive")

    return user

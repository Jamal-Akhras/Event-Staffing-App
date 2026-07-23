"""JWT token creation and validation."""

from dataclasses import dataclass
from datetime import datetime, timedelta
from uuid import uuid4

from jose import jwt, JWTError

from apps.api.src.auth.token_denylist import get_token_denylist
from apps.api.src.config import ensure_safe_startup_config, get_env

_DEFAULT_SECRET = "dev-secret-change-in-production"
JWT_SECRET_KEY = get_env("JWT_SECRET_KEY", _DEFAULT_SECRET)
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = int(get_env("JWT_EXPIRATION_HOURS", "24"))

ensure_safe_startup_config(JWT_SECRET_KEY, _DEFAULT_SECRET)


@dataclass(frozen=True)
class ResetTokenClaims:
    email: str
    issued_at: datetime


def create_access_token(data: dict) -> str:
    """Create a JWT access token.

    Args:
        data: Dictionary containing claims to encode in the token
              Should include user_id, email, role

    Returns:
        Encoded JWT token string
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS)
    to_encode["exp"] = expire
    to_encode.setdefault("jti", str(uuid4()))
    return jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def decode_access_token(token: str) -> dict:
    """Decode and validate a JWT access token, rejecting revoked tokens.

    Args:
        token: JWT token string to decode

    Returns:
        Dictionary containing the decoded claims

    Raises:
        JWTError: If token is invalid, expired, or has been revoked
    """
    payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
    jti = payload.get("jti")
    if jti and get_token_denylist().is_revoked(jti):
        raise JWTError("Token has been revoked")
    return payload


def revoke_access_token(token: str) -> None:
    """Add a token's ``jti`` to the denylist for its remaining lifetime.

    Decoding ignores expiry so an already-expired token is a harmless no-op
    (its TTL is non-positive and the denylist drops it).
    """
    payload = jwt.decode(
        token,
        JWT_SECRET_KEY,
        algorithms=[JWT_ALGORITHM],
        options={"verify_exp": False},
    )
    jti = payload.get("jti")
    if not jti:
        return
    expiry = payload.get("exp")
    if expiry is None:
        return
    remaining_seconds = int(float(expiry) - datetime.utcnow().timestamp())
    get_token_denylist().revoke(jti, remaining_seconds)


def create_reset_token(email: str) -> str:
    issued_at = datetime.utcnow()
    payload = {"email": email, "purpose": "password_reset", "iat": issued_at}
    payload["exp"] = issued_at + timedelta(hours=1)
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def decode_reset_token(token: str) -> ResetTokenClaims:
    """Returns claims from a valid password reset token. Raises JWTError if invalid."""
    payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
    if payload.get("purpose") != "password_reset":
        raise JWTError("Not a password reset token")
    email = payload.get("email")
    if not email:
        raise JWTError("Missing email in reset token")
    issued_at = payload.get("iat")
    if issued_at is None:
        raise JWTError("Missing issued-at in reset token")
    return ResetTokenClaims(email=email, issued_at=datetime.utcfromtimestamp(float(issued_at)))

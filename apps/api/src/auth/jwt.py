from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import jwt
from jwt import PyJWTError as JWTError

from apps.api.src.auth.token_denylist import get_token_denylist
from apps.api.src.config import ensure_safe_startup_config, get_env

_DEFAULT_SECRET = "dev-secret-change-in-production"
JWT_SECRET_KEY = get_env("JWT_SECRET_KEY", _DEFAULT_SECRET)
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = int(get_env("JWT_EXPIRATION_HOURS", "24"))

ensure_safe_startup_config(JWT_SECRET_KEY, _DEFAULT_SECRET)

__all__ = [
    "JWTError",
    "ResetTokenClaims",
    "create_access_token",
    "decode_access_token",
    "revoke_access_token",
    "create_reset_token",
    "decode_reset_token",
]


@dataclass(frozen=True)
class ResetTokenClaims:
    email: str
    issued_at: datetime


def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    issued_at = datetime.now(UTC)
    to_encode.setdefault("iat", issued_at)
    to_encode["exp"] = issued_at + timedelta(hours=JWT_EXPIRATION_HOURS)
    to_encode.setdefault("jti", str(uuid4()))
    return jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def decode_access_token(token: str) -> dict:
    payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
    jti = payload.get("jti")
    if jti and get_token_denylist().is_revoked(jti):
        raise JWTError("Token has been revoked")
    return payload


def revoke_access_token(token: str) -> None:
    payload = jwt.decode(
        token,
        JWT_SECRET_KEY,
        algorithms=[JWT_ALGORITHM],
        options={"verify_exp": False},
    )
    jti = payload.get("jti")
    expiry = payload.get("exp")
    if not jti or expiry is None:
        return
    remaining_seconds = int(float(expiry) - datetime.now(UTC).timestamp())
    get_token_denylist().revoke(jti, remaining_seconds)


def create_reset_token(email: str) -> str:
    issued_at = datetime.now(UTC)
    payload = {
        "email": email,
        "purpose": "password_reset",
        "iat": issued_at,
        "exp": issued_at + timedelta(hours=1),
    }
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def decode_reset_token(token: str) -> ResetTokenClaims:
    payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
    if payload.get("purpose") != "password_reset":
        raise JWTError("Not a password reset token")
    email = payload.get("email")
    issued_at = payload.get("iat")
    if not email or issued_at is None:
        raise JWTError("Reset token is missing required claims")
    return ResetTokenClaims(email=email, issued_at=datetime.fromtimestamp(float(issued_at), UTC))

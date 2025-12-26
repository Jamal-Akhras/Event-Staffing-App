"""Authentication module for JWT-based authentication."""

from apps.api.src.auth.password import hash_password, verify_password
from apps.api.src.auth.jwt import create_access_token, decode_access_token
from apps.api.src.auth.dependencies import get_current_user

__all__ = [
    "hash_password",
    "verify_password",
    "create_access_token",
    "decode_access_token",
    "get_current_user",
]

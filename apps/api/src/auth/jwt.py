"""JWT token creation and validation."""

import os
from datetime import datetime, timedelta

from jose import jwt, JWTError

JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "dev-secret-change-in-production")
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = int(os.getenv("JWT_EXPIRATION_HOURS", "24"))


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
    return jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def decode_access_token(token: str) -> dict:
    """Decode and validate a JWT access token.

    Args:
        token: JWT token string to decode

    Returns:
        Dictionary containing the decoded claims

    Raises:
        JWTError: If token is invalid or expired
    """
    return jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])

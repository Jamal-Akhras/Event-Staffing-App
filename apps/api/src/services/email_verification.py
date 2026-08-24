"""Email-verification token generation and dispatch.

Verification tokens are opaque random strings stored on the user record. On
register (worker and operator) a token is generated and a verification email is
sent via the pluggable transport. ``POST /auth/verify-email`` clears the token and
sets ``email_verified``; ``POST /auth/resend-verification`` issues a fresh token.
"""

from __future__ import annotations

import secrets

from apps.api.src.config import get_web_base_url
from apps.api.src.services.email import Email, EmailTransport


def generate_verification_token() -> str:
    return secrets.token_urlsafe(32)


def _verification_link(token: str) -> str:
    base = get_web_base_url()
    return f"{base}/verify-email?token={token}"


def send_verification_email(transport: EmailTransport, to_address: str, token: str) -> None:
    transport.send(build_verification_email(to_address, token))


def build_verification_email(to_address: str, token: str) -> Email:
    link = _verification_link(token)
    body = (
        "Welcome to the Event Staffing Platform.\n\n"
        "Please confirm your email address by opening the link below:\n"
        f"{link}\n\n"
        f"If the link does not work, use this verification token directly: {token}\n\n"
        "If you did not create this account you can ignore this message."
    )
    return Email(
        to_address=to_address,
        subject="Verify your email address",
        body=body,
    )

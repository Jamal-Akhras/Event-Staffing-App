"""Password-reset email dispatch.

Reset tokens are signed JWTs (see auth.jwt.create_reset_token) with a one-hour
expiry; nothing is stored server-side. The email links to the web reset page,
which pre-fills the token from the URL.
"""

from __future__ import annotations

from apps.api.src.config import get_web_base_url
from apps.api.src.services.email import Email, EmailTransport


def _reset_link(token: str) -> str:
    base = get_web_base_url()
    return f"{base}/reset-password?token={token}"


def send_password_reset_email(transport: EmailTransport, to_address: str, token: str) -> None:
    transport.send(build_password_reset_email(to_address, token))


def build_password_reset_email(to_address: str, token: str) -> Email:
    link = _reset_link(token)
    body = (
        "We received a request to reset your Event Staffing Platform password.\n\n"
        "Open the link below to choose a new password:\n"
        f"{link}\n\n"
        "This link expires in 1 hour. If it has expired, request a new one from "
        "the sign-in page.\n\n"
        "If you did not request this, you can ignore this message; your password "
        "will not change."
    )
    return Email(
        to_address=to_address,
        subject="Reset your password",
        body=body,
    )

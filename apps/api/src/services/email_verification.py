from __future__ import annotations

import secrets

from apps.api.src.config import get_web_base_url
from apps.api.src.services.email import Email


def generate_verification_token() -> str:
    return secrets.token_urlsafe(32)


def build_verification_email(to_address: str, token: str) -> Email:
    link = f"{get_web_base_url()}/verify-email?token={token}"
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

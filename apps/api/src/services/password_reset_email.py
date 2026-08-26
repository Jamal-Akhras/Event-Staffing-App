from __future__ import annotations

from apps.api.src.config import get_web_base_url
from apps.api.src.services.email import Email


def build_password_reset_email(to_address: str, token: str) -> Email:
    link = f"{get_web_base_url()}/reset-password?token={token}"
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

"""Operator sign-up invite codes.

Operator registration grants venue privileges, so it must not be open. Valid invite
codes are configured via the OPERATOR_INVITE_CODES env var (comma-separated). This is
the simplest correct gate for now; a future phase can move codes into the database with
per-code usage limits and expiry.
"""

from __future__ import annotations

from apps.api.src.config import get_env


def _valid_invite_codes() -> set[str]:
    raw = get_env("OPERATOR_INVITE_CODES")
    return {code.strip() for code in raw.split(",") if code.strip()}


def is_valid_invite_code(code: str | None) -> bool:
    if not code:
        return False
    return code.strip() in _valid_invite_codes()

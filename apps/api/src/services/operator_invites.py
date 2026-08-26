from __future__ import annotations

from apps.api.src.config import get_env


def _valid_invite_codes() -> set[str]:
    raw = get_env("OPERATOR_INVITE_CODES")
    return {code.strip() for code in raw.split(",") if code.strip()}


def is_valid_invite_code(code: str | None) -> bool:
    if not code:
        return False
    return code.strip() in _valid_invite_codes()

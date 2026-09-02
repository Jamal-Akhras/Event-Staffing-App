from __future__ import annotations

import secrets

UNAMBIGUOUS_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"


def new_code(prefix: str) -> str:
    normalized = prefix.strip().upper()
    if not normalized or len(normalized) > 21 or not normalized.isalnum():
        raise ValueError("prefix must contain 1-21 letters or numbers")
    body = "".join(secrets.choice(UNAMBIGUOUS_ALPHABET) for _ in range(8))
    return f"{normalized}-{body[:4]}-{body[4:]}"

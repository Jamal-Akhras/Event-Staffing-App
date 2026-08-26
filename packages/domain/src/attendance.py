from __future__ import annotations

import secrets


def new_attendance_code(excluding: str | None = None) -> str:
    code = f"{secrets.randbelow(10_000):04d}"
    while code == excluding:
        code = f"{secrets.randbelow(10_000):04d}"
    return code


def code_matches(submitted: str | None, expected: str) -> bool:
    return submitted is not None and secrets.compare_digest(submitted, expected)

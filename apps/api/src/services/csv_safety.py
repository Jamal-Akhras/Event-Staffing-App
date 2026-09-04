from __future__ import annotations

from typing import Any


def escape_csv_formula(value: Any) -> str:
    text = str(value)
    if text and text[0] in ("=", "+", "-", "@"):
        return "'" + text
    return text

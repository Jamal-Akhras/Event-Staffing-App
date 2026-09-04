from __future__ import annotations

from dataclasses import dataclass
import re


@dataclass
class Deidentified:
    fields: dict[str, str]
    rehydration: dict[str, str]


def deidentify(pairs: dict[str, str | None]) -> Deidentified:
    fields: dict[str, str] = {}
    rehydration: dict[str, str] = {}
    for key, value in pairs.items():
        if value is None:
            continue
        placeholder = "{" + key + "}"
        fields[key] = placeholder
        rehydration[placeholder] = str(value)
    return Deidentified(fields=fields, rehydration=rehydration)


def rehydrate(text: str, rehydration: dict[str, str]) -> str:
    if not rehydration:
        return text
    placeholders = sorted(rehydration, key=len, reverse=True)
    pattern = re.compile("|".join(re.escape(placeholder) for placeholder in placeholders))
    return pattern.sub(lambda match: rehydration[match.group(0)], text)

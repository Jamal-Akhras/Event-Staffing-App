from __future__ import annotations

from dataclasses import dataclass


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
    for placeholder, value in rehydration.items():
        text = text.replace(placeholder, value)
    return text

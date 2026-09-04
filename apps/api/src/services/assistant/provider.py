from __future__ import annotations

import logging
from typing import Protocol

log = logging.getLogger(__name__)

SHIFT_POST = "shift_post"
OFFER_MESSAGE = "offer_message"


class AssistantProvider(Protocol):
    def generate(self, kind: str, fields: dict[str, str]) -> str:
        ...


class DeterministicAssistant:
    def generate(self, kind: str, fields: dict[str, str]) -> str:
        if kind == SHIFT_POST:
            return _shift_post(fields)
        if kind == OFFER_MESSAGE:
            return _offer_message(fields)
        raise ValueError(f"Unknown assistant kind: {kind}")


class GuardedProvider:
    def __init__(self, primary: AssistantProvider, fallback: AssistantProvider) -> None:
        self._primary = primary
        self._fallback = fallback

    def generate(self, kind: str, fields: dict[str, str]) -> str:
        try:
            return self._primary.generate(kind, fields)
        except Exception:
            log.exception("assistant primary provider failed; using deterministic fallback")
            return self._fallback.generate(kind, fields)


def _shift_post(f: dict[str, str]) -> str:
    role = f.get("role", "team member")
    venue = f.get("venue", "our venue")
    location = f.get("location", "")
    timing = f.get("timing", "")
    day = f.get("day", "")
    rate = f.get("rate", "")
    note = f.get("note", "")
    place = f" in {location}" if location else ""
    lines = [
        f"**{role} at {venue}**",
        f"Join the team at {venue}{place} for a {timing} shift. "
        f"You'll keep service running and guests looked after.",
    ]
    if note:
        lines.append(note)
    why = "Why this shift:"
    if rate and day:
        why += f" {rate} an hour on a {day} evening."
    elif rate:
        why += f" {rate} an hour."
    else:
        why += " a solid shift with a friendly team."
    lines.append(why)
    return "\n\n".join(lines)


def _offer_message(f: dict[str, str]) -> str:
    worker = f.get("worker", "there")
    role = f.get("role", "shift")
    date = f.get("date", "soon")
    time = f.get("time", "")
    venue = f.get("venue", "us")
    rate = f.get("rate", "")
    when = f"{date}, {time}" if time else date
    money = f" at {rate} an hour" if rate else ""
    return (
        f"Hi {worker}! Hope you're well. We've got a {role} shift at {venue} on "
        f"{when}{money}, and we'd love to have you on it. Would you be up for it? "
        "No pressure either way."
    )

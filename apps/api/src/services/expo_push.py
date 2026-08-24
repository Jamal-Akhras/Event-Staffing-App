from __future__ import annotations

import json
from urllib.request import Request, urlopen

from apps.api.src.config import get_env


def send_expo_push(
    tokens: list[str],
    title: str,
    body: str,
    data: dict[str, object],
) -> None:
    if not tokens:
        return
    messages = [
        {"to": token, "title": title, "body": body, "data": data, "sound": "default"}
        for token in tokens
    ]
    request = Request(
        get_env("EXPO_PUSH_URL", "https://exp.host/--/api/v2/push/send"),
        data=json.dumps(messages).encode("utf-8"),
        headers={"Accept": "application/json", "Content-Type": "application/json"},
        method="POST",
    )
    with urlopen(request, timeout=15) as response:
        payload = json.loads(response.read().decode("utf-8"))
    tickets = payload.get("data")
    if not isinstance(tickets, list) or len(tickets) != len(tokens):
        raise RuntimeError("Expo push returned an invalid ticket response.")
    errors = [ticket for ticket in tickets if ticket.get("status") == "error"]
    if errors:
        raise RuntimeError(f"Expo push rejected {len(errors)} notification(s).")

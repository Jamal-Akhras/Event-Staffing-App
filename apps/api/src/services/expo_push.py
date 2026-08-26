from __future__ import annotations

from urllib.parse import urlparse

from exponent_server_sdk import (
    DeviceNotRegisteredError,
    PushClient,
    PushMessage,
    PushServerError,
    PushTicketError,
)

from apps.api.src.config import get_env

DEFAULT_PUSH_URL = "https://exp.host/--/api/v2/push/send"


def send_expo_push(tokens: list[str], title: str, body: str, data: dict[str, object]) -> list[str]:
    if not tokens:
        return []
    messages = [
        PushMessage(to=token, title=title, body=body, data=data, sound="default")
        for token in tokens
    ]
    try:
        tickets = _client().publish_multiple(messages)
    except PushServerError as exc:
        raise RuntimeError(f"Expo push server error: {exc}") from exc
    dead_tokens: list[str] = []
    for ticket in tickets:
        try:
            ticket.validate_response()
        except DeviceNotRegisteredError:
            dead_tokens.append(ticket.push_message.to)
        except PushTicketError as exc:
            raise RuntimeError(f"Expo push rejected a notification: {ticket.message}") from exc
    return dead_tokens


def _client() -> PushClient:
    push_url = urlparse(get_env("EXPO_PUSH_URL", DEFAULT_PUSH_URL))
    host = f"{push_url.scheme}://{push_url.netloc}"
    api_url = push_url.path.removesuffix("/push/send")
    return PushClient(host=host, api_url=api_url, timeout=15)

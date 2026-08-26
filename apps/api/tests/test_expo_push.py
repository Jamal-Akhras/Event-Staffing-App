from __future__ import annotations

import pytest
from exponent_server_sdk import PushClient, PushServerError, PushTicket

from apps.api.src.services.expo_push import send_expo_push


def _ticket(message, status: str, error: str | None = None) -> PushTicket:
    details = {"error": error} if error else None
    return PushTicket(push_message=message, status=status, message=error, details=details, id="t")


def test_dead_tokens_are_returned_and_good_ones_are_not(monkeypatch):
    def fake_publish(self, messages):
        return [
            _ticket(messages[0], PushTicket.SUCCESS_STATUS),
            _ticket(messages[1], PushTicket.ERROR_STATUS, PushTicket.ERROR_DEVICE_NOT_REGISTERED),
        ]

    monkeypatch.setattr(PushClient, "publish_multiple", fake_publish)

    dead = send_expo_push(["ExponentPushToken[live]", "ExponentPushToken[gone]"], "Hi", "Body", {})

    assert dead == ["ExponentPushToken[gone]"]


def test_other_ticket_errors_and_server_errors_raise(monkeypatch):
    monkeypatch.setattr(
        PushClient,
        "publish_multiple",
        lambda self, messages: [_ticket(messages[0], PushTicket.ERROR_STATUS, PushTicket.ERROR_MESSAGE_TOO_BIG)],
    )
    with pytest.raises(RuntimeError):
        send_expo_push(["ExponentPushToken[a]"], "Hi", "Body", {})

    def boom(self, messages):
        raise PushServerError("down", None)

    monkeypatch.setattr(PushClient, "publish_multiple", boom)
    with pytest.raises(RuntimeError):
        send_expo_push(["ExponentPushToken[a]"], "Hi", "Body", {})


def test_empty_token_list_sends_nothing(monkeypatch):
    monkeypatch.setattr(PushClient, "publish_multiple", lambda self, messages: pytest.fail("should not publish"))

    assert send_expo_push([], "Hi", "Body", {}) == []

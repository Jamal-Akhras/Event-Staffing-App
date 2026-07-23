"""Pluggable email delivery for verification and other transactional messages.

Two transports, selected by environment:
- ``LoggingEmailTransport`` (dev/test default): logs the recipient, subject and body
  instead of sending. No external service, no credentials. The verification link is
  visible in the application log so flows can be exercised end to end locally.
- ``SmtpEmailTransport``: sends via stdlib smtplib using SMTP_HOST/PORT/USER/PASSWORD/FROM.
  Selected when EMAIL_TRANSPORT=smtp (or SMTP_HOST is set outside development).

Failures are never swallowed: if SMTP is configured and a send fails, the exception
propagates so the caller surfaces it rather than silently dropping the email.
"""

from __future__ import annotations

import logging
import smtplib
from dataclasses import dataclass
from email.message import EmailMessage
from typing import Protocol

from apps.api.src.config import get_env, is_development

log = logging.getLogger(__name__)


@dataclass(frozen=True)
class Email:
    to_address: str
    subject: str
    body: str


class EmailTransport(Protocol):
    def send(self, email: Email) -> None:
        raise NotImplementedError


class LoggingEmailTransport:
    def send(self, email: Email) -> None:
        log.info(
            "DEV email (not actually sent) -> to=%s subject=%s\n%s",
            email.to_address,
            email.subject,
            email.body,
        )


@dataclass(frozen=True)
class SmtpSettings:
    host: str
    port: int
    username: str
    password: str
    from_address: str

    @classmethod
    def from_env(cls) -> "SmtpSettings":
        host = get_env("SMTP_HOST")
        if not host:
            raise RuntimeError("SMTP_HOST must be set to use the SMTP email transport.")
        from_address = get_env("SMTP_FROM")
        if not from_address:
            raise RuntimeError("SMTP_FROM must be set to use the SMTP email transport.")
        return cls(
            host=host,
            port=int(get_env("SMTP_PORT", "587")),
            username=get_env("SMTP_USER"),
            password=get_env("SMTP_PASSWORD"),
            from_address=from_address,
        )


class SmtpEmailTransport:
    def __init__(self, settings: SmtpSettings) -> None:
        self._settings = settings

    def send(self, email: Email) -> None:
        message = EmailMessage()
        message["From"] = self._settings.from_address
        message["To"] = email.to_address
        message["Subject"] = email.subject
        message.set_content(email.body)

        with smtplib.SMTP(self._settings.host, self._settings.port, timeout=15) as server:
            server.starttls()
            if self._settings.username:
                server.login(self._settings.username, self._settings.password)
            server.send_message(message)


def _select_transport() -> EmailTransport:
    transport_name = get_env("EMAIL_TRANSPORT").strip().lower()
    if transport_name == "smtp":
        return SmtpEmailTransport(SmtpSettings.from_env())
    if transport_name == "logging":
        return LoggingEmailTransport()
    if not is_development() and get_env("SMTP_HOST"):
        return SmtpEmailTransport(SmtpSettings.from_env())
    return LoggingEmailTransport()


_transport: EmailTransport = _select_transport()


def get_email_transport() -> EmailTransport:
    return _transport

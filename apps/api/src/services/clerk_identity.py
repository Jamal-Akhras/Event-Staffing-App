from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

import httpx
import jwt
from jwt import PyJWKClient, PyJWKClientError, PyJWTError

from apps.api.src.config import get_env

CLERK_BACKEND_API = "https://api.clerk.com/v1"


@dataclass(frozen=True)
class SsoIdentity:
    provider: str
    subject: str
    email: str
    email_verified: bool
    display_name: str | None


class IdentityVerificationError(Exception):
    pass


class IdentityVerifier(Protocol):
    def verify(self, token: str) -> SsoIdentity: ...


@dataclass(frozen=True)
class ClerkSettings:
    issuer: str
    secret_key: str
    authorized_parties: tuple[str, ...]


def get_clerk_settings() -> ClerkSettings | None:
    issuer = get_env("CLERK_ISSUER").strip().rstrip("/")
    if not issuer:
        return None
    secret_key = get_env("CLERK_SECRET_KEY").strip()
    if not secret_key:
        raise RuntimeError("CLERK_SECRET_KEY must be set when CLERK_ISSUER is configured.")
    parties = tuple(
        party.strip().rstrip("/")
        for party in get_env("CLERK_AUTHORIZED_PARTIES").split(",")
        if party.strip()
    )
    return ClerkSettings(issuer, secret_key, parties)


class ClerkIdentityVerifier:
    def __init__(
        self,
        settings: ClerkSettings,
        http: httpx.Client | None = None,
        jwk_client: PyJWKClient | None = None,
    ) -> None:
        self._settings = settings
        self._http = http or httpx.Client(timeout=5.0)
        self._jwks = jwk_client or PyJWKClient(f"{settings.issuer}/.well-known/jwks.json", cache_keys=True)

    def verify(self, token: str) -> SsoIdentity:
        try:
            signing_key = self._jwks.get_signing_key_from_jwt(token)
            claims = jwt.decode(
                token,
                signing_key.key,
                algorithms=["RS256"],
                issuer=self._settings.issuer,
                options={"verify_aud": False},
            )
        except (PyJWKClientError, PyJWTError) as exc:
            raise IdentityVerificationError("Sign-in token was rejected.") from exc
        authorized_party = claims.get("azp")
        if (
            authorized_party
            and self._settings.authorized_parties
            and authorized_party.rstrip("/") not in self._settings.authorized_parties
        ):
            raise IdentityVerificationError("Sign-in token was issued for another application.")
        subject = claims.get("sub")
        if not subject:
            raise IdentityVerificationError("Sign-in token has no subject.")
        email = claims.get("email")
        if email:
            return SsoIdentity("clerk", subject, email.lower(), True, claims.get("name"))
        return self._fetch_identity(subject)

    def _fetch_identity(self, subject: str) -> SsoIdentity:
        response = self._http.get(
            f"{CLERK_BACKEND_API}/users/{subject}",
            headers={"Authorization": f"Bearer {self._settings.secret_key}"},
        )
        if response.status_code != 200:
            raise IdentityVerificationError("Could not load the signed-in identity.")
        data = response.json()
        primary_id = data.get("primary_email_address_id")
        primary = next(
            (entry for entry in data.get("email_addresses", []) if entry.get("id") == primary_id),
            None,
        )
        if primary is None or not primary.get("email_address"):
            raise IdentityVerificationError("The signed-in identity has no email address.")
        verified = (primary.get("verification") or {}).get("status") == "verified"
        name = " ".join(part for part in (data.get("first_name"), data.get("last_name")) if part) or None
        return SsoIdentity("clerk", subject, primary["email_address"].lower(), verified, name)

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import jwt
import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

from apps.api.src.services.clerk_identity import (
    ClerkIdentityVerifier,
    ClerkSettings,
    IdentityVerificationError,
)

ISSUER = "https://test.clerk.accounts.dev"
SETTINGS = ClerkSettings(ISSUER, "sk_test", ("http://localhost:5173",))


class StaticJwks:
    def __init__(self, public_pem: bytes) -> None:
        self._key = serialization.load_pem_public_key(public_pem)

    def get_signing_key_from_jwt(self, token: str):
        return type("Key", (), {"key": self._key})()


@pytest.fixture(scope="module")
def keypair():
    private = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    private_pem = private.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption(),
    )
    public_pem = private.public_key().public_bytes(
        serialization.Encoding.PEM,
        serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    return private_pem, public_pem


def _token(private_pem: bytes, **overrides) -> str:
    now = datetime.now(UTC)
    claims = {
        "iss": ISSUER,
        "sub": "user_123",
        "azp": "http://localhost:5173",
        "iat": now,
        "nbf": now,
        "exp": now + timedelta(minutes=1),
        "email": "Priya@Example.com",
        **overrides,
    }
    return jwt.encode(claims, private_pem, algorithm="RS256", headers={"kid": "k1"})


def _verifier(public_pem: bytes) -> ClerkIdentityVerifier:
    return ClerkIdentityVerifier(SETTINGS, jwk_client=StaticJwks(public_pem))


def test_valid_token_yields_identity_from_email_claim(keypair):
    private_pem, public_pem = keypair

    identity = _verifier(public_pem).verify(_token(private_pem))

    assert identity.subject == "user_123"
    assert identity.email == "priya@example.com"
    assert identity.email_verified is True


def test_wrong_issuer_expired_and_foreign_party_are_rejected(keypair):
    private_pem, public_pem = keypair
    verifier = _verifier(public_pem)

    for bad in (
        _token(private_pem, iss="https://other.example"),
        _token(private_pem, exp=datetime.now(UTC) - timedelta(minutes=1)),
        _token(private_pem, azp="https://evil.example"),
    ):
        with pytest.raises(IdentityVerificationError):
            verifier.verify(bad)


def test_token_signed_by_another_key_is_rejected(keypair):
    _, public_pem = keypair
    other = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    other_pem = other.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption(),
    )

    with pytest.raises(IdentityVerificationError):
        _verifier(public_pem).verify(_token(other_pem))

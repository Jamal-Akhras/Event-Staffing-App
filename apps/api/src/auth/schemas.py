from typing import Annotated, Literal

from pydantic import BaseModel, BeforeValidator, EmailStr, Field, model_validator

from apps.api.src.validation_types import UtcTimestamp


def _normalize_email(value: object) -> object:
    return value.strip().lower() if isinstance(value, str) else value


NormalizedEmail = Annotated[EmailStr, BeforeValidator(_normalize_email)]


class UserRegisterRequest(BaseModel):
    email: NormalizedEmail
    password: str = Field(min_length=8, max_length=128)


class OperatorRegisterRequest(BaseModel):
    email: NormalizedEmail
    password: str | None = Field(default=None, min_length=8, max_length=128)
    sso_token: str | None = Field(default=None, min_length=20, max_length=4096)
    venue_name: str = Field(min_length=1, max_length=160)
    organisation_name: str | None = Field(default=None, max_length=160)
    country: str = Field(min_length=2, max_length=2)
    market_id: str = Field(min_length=1, max_length=100)
    invite_code: str = Field(min_length=1, max_length=200)

    @model_validator(mode="after")
    def _require_one_credential(self) -> "OperatorRegisterRequest":
        if (self.password is None) == (self.sso_token is None):
            raise ValueError("Provide either a password or a sign-in token, not both.")
        return self


class SsoSignInRequest(BaseModel):
    token: str = Field(min_length=20, max_length=4096)
    role: Literal["worker", "operator"] = "worker"


class UserLoginRequest(BaseModel):
    email: NormalizedEmail
    password: str = Field(min_length=1, max_length=128)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str
    email: str
    role: str
    account_id: str | None = None
    organisation_id: str | None = None
    venue_id: str | None = None
    worker_profile_id: str | None = None
    currency: str = "GBP"
    email_verified: bool = False


class LogoutResponse(BaseModel):
    message: str


class VerifyEmailRequest(BaseModel):
    token: str = Field(min_length=1, max_length=200)


class ResendVerificationRequest(BaseModel):
    email: NormalizedEmail


class EmailVerificationResponse(BaseModel):
    message: str
    email_verified: bool = False


class SessionResponse(BaseModel):
    user_id: str
    role: str
    tenant_id: str | None
    organisation_id: str | None
    venue_id: str | None
    auth_mode: str
    data_scope: str


class UserResponse(BaseModel):
    user_id: str
    email: str
    role: str
    worker_profile_id: str | None
    is_active: bool
    created_at: UtcTimestamp


class ForgotPasswordRequest(BaseModel):
    email: NormalizedEmail


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(min_length=8, max_length=128)


class PasswordResetResponse(BaseModel):
    message: str
    reset_token: str | None = None

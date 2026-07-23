"""Authentication request/response schemas."""

from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class UserRegisterRequest(BaseModel):
    """Request schema for user registration."""

    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class OperatorRegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    venue_name: str
    country: str  # "GB" or "AE"
    invite_code: str


class UserLoginRequest(BaseModel):
    """Request schema for user login."""

    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    """Response schema for authentication endpoints."""

    access_token: str
    token_type: str = "bearer"
    user_id: str
    email: str
    role: str
    account_id: str | None = None
    worker_profile_id: str | None = None
    currency: str = "GBP"
    email_verified: bool = False


class LogoutResponse(BaseModel):
    message: str


class VerifyEmailRequest(BaseModel):
    token: str


class ResendVerificationRequest(BaseModel):
    email: EmailStr


class EmailVerificationResponse(BaseModel):
    message: str
    email_verified: bool = False


class SessionResponse(BaseModel):
    user_id: str
    role: str
    tenant_id: str | None
    auth_mode: str
    data_scope: str


class UserResponse(BaseModel):
    """Response schema for user information."""

    user_id: str
    email: str
    role: str
    worker_profile_id: str | None
    is_active: bool
    created_at: datetime


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(min_length=8, max_length=128)


class PasswordResetResponse(BaseModel):
    message: str
    reset_token: str | None = None

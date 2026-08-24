from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

from apps.api.src.validation_types import UtcTimestamp


class AccountExportRequest(BaseModel):
    password: str = Field(min_length=1, max_length=128)


class AccountExportResponse(BaseModel):
    generated_at: UtcTimestamp
    user_id: str
    data: dict[str, Any]


class AccountDeactivateRequest(BaseModel):
    password: str = Field(min_length=1, max_length=128)
    confirmation: Literal["DELETE"]


class AccountDeactivateResponse(BaseModel):
    message: str

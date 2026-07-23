from __future__ import annotations

from typing import NoReturn

from fastapi import HTTPException

from apps.api.src.services.errors import (
    ConflictError,
    ForbiddenError,
    NotFoundError,
    ServiceError,
    ValidationError,
)


def raise_service_error(exc: ServiceError) -> NoReturn:
    if isinstance(exc, NotFoundError):
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    if isinstance(exc, ValidationError):
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if isinstance(exc, ConflictError):
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    if isinstance(exc, ForbiddenError):
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    raise HTTPException(status_code=500, detail="Internal service error.") from exc

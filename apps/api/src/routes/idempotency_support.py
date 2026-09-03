from __future__ import annotations

from typing import Annotated, TypeVar

from fastapi import Header, HTTPException, Response
from pydantic import BaseModel

from apps.api.src.services.idempotency import (
    IdempotencyConflict,
    IdempotencyService,
    IdempotencyStart,
)

IdempotencyKeyHeader = Annotated[
    str | None,
    Header(alias="Idempotency-Key", min_length=1, max_length=100, pattern="^[A-Za-z0-9._:-]+$"),
]

ResponseModel = TypeVar("ResponseModel", bound=BaseModel)


def replayed(response: Response, model: type[ResponseModel], cached: dict) -> ResponseModel:
    response.headers["Idempotency-Replayed"] = "true"
    return model.model_validate(cached)


def start_or_conflict(
    service: IdempotencyService,
    user_id: str,
    scope: str,
    key: str | None,
    payload: dict,
) -> IdempotencyStart:
    try:
        return service.start(user_id, scope, key, payload)
    except IdempotencyConflict as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc

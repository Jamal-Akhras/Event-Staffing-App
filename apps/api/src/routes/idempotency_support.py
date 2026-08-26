from __future__ import annotations

from typing import Annotated, TypeVar

from fastapi import Header, Response
from pydantic import BaseModel

IdempotencyKeyHeader = Annotated[
    str | None,
    Header(alias="Idempotency-Key", min_length=1, max_length=100, pattern="^[A-Za-z0-9._:-]+$"),
]

ResponseModel = TypeVar("ResponseModel", bound=BaseModel)


def replayed(response: Response, model: type[ResponseModel], cached: dict) -> ResponseModel:
    response.headers["Idempotency-Replayed"] = "true"
    return model(**cached)

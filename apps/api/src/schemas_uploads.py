from __future__ import annotations

from pydantic import BaseModel


class UploadResponse(BaseModel):
    url: str
    filename: str

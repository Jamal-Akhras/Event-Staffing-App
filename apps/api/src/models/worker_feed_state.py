from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class WorkerFeedState(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    worker_id: str
    shift_id: str
    action: str
    created_at: datetime
    updated_at: datetime

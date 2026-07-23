from __future__ import annotations

import os

os.environ["USE_IN_MEMORY"] = "true"
os.environ["DEV_MODE"] = "true"

import pytest


@pytest.fixture(autouse=True)
def reset_rate_limiter():
    from apps.api.src.main import app
    app.state.limiter.reset()
    yield
    app.state.limiter.reset()

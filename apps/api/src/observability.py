from __future__ import annotations

import logging

from apps.api.src.config import get_env, get_environment

log = logging.getLogger(__name__)


def init_sentry() -> None:
    """Initialize Sentry if SENTRY_DSN is set. No-op otherwise."""
    dsn = get_env("SENTRY_DSN", "")
    if not dsn:
        return
    try:
        import sentry_sdk
        from sentry_sdk.integrations.fastapi import FastApiIntegration
        from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
    except ImportError:
        log.warning("SENTRY_DSN set but sentry-sdk is not installed; skipping init.")
        return

    sentry_sdk.init(
        dsn=dsn,
        environment=get_environment(),
        integrations=[FastApiIntegration(), SqlalchemyIntegration()],
        traces_sample_rate=float(get_env("SENTRY_TRACES_SAMPLE_RATE", "0.0")),
        send_default_pii=False,
    )
    log.info("Sentry initialized (env=%s)", get_environment())

from __future__ import annotations

import os
import subprocess
import sys


def _run_import(env_overrides: dict[str, str]) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env.update(env_overrides)
    return subprocess.run(
        [sys.executable, "-c", "import apps.api.src.auth.jwt"],
        capture_output=True,
        env=env,
        text=True,
    )


def test_guard_raises_in_production_with_dev_mode() -> None:
    result = _run_import(
        {
            "ENVIRONMENT": "production",
            "DEV_MODE": "true",
            "JWT_SECRET_KEY": "a" * 32,
        },
    )

    assert result.returncode != 0
    assert "RuntimeError" in result.stderr
    assert "DEV_MODE" in result.stderr


def test_guard_raises_in_production_with_short_secret() -> None:
    result = _run_import(
        {
            "ENVIRONMENT": "production",
            "DEV_MODE": "false",
            "JWT_SECRET_KEY": "short",
        },
    )

    assert result.returncode != 0
    assert "RuntimeError" in result.stderr
    assert "JWT_SECRET_KEY" in result.stderr


def test_guard_raises_in_production_with_default_secret() -> None:
    result = _run_import(
        {
            "ENVIRONMENT": "production",
            "DEV_MODE": "false",
            "JWT_SECRET_KEY": "dev-secret-change-in-production",
        },
    )

    assert result.returncode != 0
    assert "RuntimeError" in result.stderr
    assert "JWT_SECRET_KEY" in result.stderr


def test_guard_is_noop_in_development() -> None:
    result = _run_import(
        {
            "ENVIRONMENT": "development",
            "DEV_MODE": "true",
            "JWT_SECRET_KEY": "dev-secret-change-in-production",
        },
    )

    assert result.returncode == 0, result.stderr

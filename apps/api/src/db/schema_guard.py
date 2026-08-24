from __future__ import annotations

from alembic.config import Config
from alembic.script import ScriptDirectory
from sqlalchemy import text

from apps.api.src.config import PROJECT_ROOT, use_in_memory_repositories


def ensure_schema_current() -> None:
    if use_in_memory_repositories():
        return
    from apps.api.src.db.database import engine

    config = Config(str(PROJECT_ROOT / "apps" / "api" / "alembic.ini"))
    expected = ScriptDirectory.from_config(config).get_current_head()
    with engine.connect() as connection:
        current = connection.execute(text("SELECT version_num FROM alembic_version")).scalar_one_or_none()
    if current != expected:
        raise RuntimeError(
            f"Database schema revision is {current or 'missing'}; expected {expected}. Run Alembic migrations before startup."
        )

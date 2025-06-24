from __future__ import annotations

from typing import Callable, Dict

from sqlalchemy import text
from sqlalchemy.engine import Engine

from .models import Base

# Define migration callbacks keyed by version number
MIGRATIONS: Dict[int, Callable[[Engine], None]] = {}


def _migration_1(engine: Engine) -> None:
    """Initial schema creation."""

    Base.metadata.create_all(engine)


# Register migration functions
MIGRATIONS[1] = _migration_1


def get_current_version(engine: Engine) -> int:
    with engine.begin() as conn:
        conn.execute(
            text(
                "CREATE TABLE IF NOT EXISTS schema_version (version INTEGER PRIMARY KEY)"
            )
        )
        val = conn.execute(text("SELECT MAX(version) FROM schema_version")).scalar()
        return int(val or 0)


def set_version(engine: Engine, version: int) -> None:
    with engine.begin() as conn:
        conn.execute(text("INSERT INTO schema_version (version) VALUES (:v)"), {"v": version})


def run_migrations(engine: Engine) -> None:
    """Apply any outstanding migrations in order."""

    current = get_current_version(engine)
    for ver in sorted(MIGRATIONS):
        if ver > current:
            MIGRATIONS[ver](engine)
            set_version(engine, ver)

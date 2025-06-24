from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path
from typing import Generator, Optional

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import QueuePool

_DEFAULT_DB_PATH = Path("data/market_data.db")


def _build_db_url(db_path: Path | str | None = None) -> str:
    if db_path is None:
        db_path = _DEFAULT_DB_PATH
    db_path = Path(db_path)
    if not db_path.parent.exists():
        db_path.parent.mkdir(parents=True, exist_ok=True)
    return f"sqlite:///{db_path.as_posix()}"


def get_engine(db_url: Optional[str] = None, pool_size: int = 5) -> Engine:
    """Return a SQLAlchemy engine with connection pooling."""

    db_url = db_url or _build_db_url(None)
    connect_args = {"check_same_thread": False} if db_url.startswith("sqlite") else {}
    engine = create_engine(
        db_url,
        echo=False,
        poolclass=QueuePool,
        pool_size=pool_size,
        connect_args=connect_args,
    )
    return engine


# Lazy global engine for convenience
_ENGINE: Optional[Engine] = None
_SessionLocal: Optional[sessionmaker] = None


def init_engine(db_url: Optional[str] = None) -> Engine:
    global _ENGINE, _SessionLocal  # noqa: PLW0603
    if _ENGINE is None:
        _ENGINE = get_engine(db_url)
        _SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=_ENGINE)
    return _ENGINE


@contextmanager
def get_session() -> Generator[Session, None, None]:
    """Provide a transactional scope around a series of operations."""

    if _ENGINE is None or _SessionLocal is None:
        init_engine()
    assert _SessionLocal is not None  # Guard for mypy
    session: Session = _SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

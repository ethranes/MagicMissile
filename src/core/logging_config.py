from __future__ import annotations

from functools import wraps
from pathlib import Path
from time import perf_counter
from typing import Callable, Iterable
import uuid
import contextvars

from loguru import logger

# Context variable that stores correlation ID per logical context (e.g., request)
_correlation_id_ctx: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "correlation_id", default=None
)


def new_correlation_id() -> str:
    """Generate a new correlation ID and set it in context."""

    cid = uuid.uuid4().hex[:12]
    _correlation_id_ctx.set(cid)
    return cid


def get_correlation_id() -> str | None:
    """Return current correlation ID or None."""

    return _correlation_id_ctx.get()


def _inject_correlation_id(record: dict) -> bool:
    """Loguru filter to inject correlation_id into each record."""

    record["extra"]["correlation_id"] = get_correlation_id() or "-"
    return True


def log_timing(name: str | None = None) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """Decorator to log execution time of a function.

    Args:
        name: Optional name for the timed block; defaults to function.__name__.
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args, **kwargs):  # type: ignore[no-any-unbound]
            start = perf_counter()
            try:
                return func(*args, **kwargs)
            finally:
                duration_ms = (perf_counter() - start) * 1000
                logger.info(
                    f"{name or func.__name__} executed in {duration_ms:.2f} ms",
                    extra={"metric": "timing", "duration_ms": duration_ms},
                )

        return wrapper  # type: ignore[return-value]

    return decorator


T = "T"


def setup_logging(log_dir: str | Path = "logs", level: str = "INFO") -> None:
    """Configure loguru logging.

    Args:
        log_dir: Directory to store log files.
        level: Logging level.
    """

    log_dir = Path(log_dir)
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "app.log"

    # Remove default handler to avoid duplicate logs
    logger.remove()

    fmt = "{time:YYYY-MM-DD HH:mm:ss.SSS} | {level:^8} | {extra[correlation_id]} | {message}"

    # Console handler
    logger.add(
        lambda msg: print(msg, end=""),
        level=level,
        format=fmt,
        filter=_inject_correlation_id,
    )

    # File handler with rotation and retention
    logger.add(
        log_file,
        level=level,
        format=fmt,
        filter=_inject_correlation_id,
        rotation="10 MB",
        retention="10 days",
        compression="zip",
        enqueue=True,
        backtrace=True,
        diagnose=True,
    )

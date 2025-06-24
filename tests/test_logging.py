from pathlib import Path

from loguru import logger

from src.core.logging_config import (
    get_correlation_id,
    log_timing,
    new_correlation_id,
    setup_logging,
)


def test_correlation_id(tmp_path: Path) -> None:
    # Configure logging to temp dir
    setup_logging(log_dir=tmp_path, level="INFO")

    # No correlation id initially
    assert get_correlation_id() is None

    cid = new_correlation_id()
    assert get_correlation_id() == cid

    logger.bind(test="yes").info("message with cid")


def test_log_timing_decorator(caplog) -> None:
    setup_logging(level="INFO")

    @log_timing()
    def sample():
        lst = [i for i in range(1000)]
        return sum(lst)

    result = sample()
    assert result == sum(range(1000))

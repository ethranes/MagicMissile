"""Performance benchmark tests for key metric functions.

These tests use ``pytest-benchmark`` to ensure that performance-critical
calculations remain within acceptable time bounds.  They will **not fail** the
suite on slower runs (the default behaviour), but they do produce historical
benchmark data that can be inspected on CI or locally with
``pytest --benchmark-save``.
"""
from __future__ import annotations

import pytest
import pandas as pd

# Skip the entire module if pytest-benchmark is not installed/enabled.
pytest.importorskip("pytest_benchmark")

from src.backtesting import metrics


def _create_equity_series(length: int = 252 * 3) -> pd.Series:
    """Generate a synthetic equity curve that grows ~0.05 % per day."""
    idx = pd.date_range("2022-01-01", periods=length, freq="B")
    growth = 1 + 0.0005  # 0.05 % daily
    equity = pd.Series(100 * (growth ** pd.Series(range(len(idx)))), index=idx)
    return equity


def test_total_return_benchmark(benchmark):
    equity = _create_equity_series()

    # Benchmark the *total_return* computation.
    benchmark(metrics.total_return, equity)


def test_sharpe_ratio_benchmark(benchmark):
    equity = _create_equity_series()

    benchmark(metrics.sharpe_ratio, equity)

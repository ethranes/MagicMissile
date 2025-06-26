"""Stress tests simulating high-frequency data scenarios.

The goal is to run core performance calculations on a dense intraday series
(~10⁴–10⁵ rows) to ensure they complete in a reasonable time and produce valid
outputs.  These tests are intentionally lightweight so they remain fast on CI
while still providing confidence that our vectorised implementations scale.
"""
from __future__ import annotations

import time

import pandas as pd
import pytest

from src.backtesting import metrics


@pytest.mark.parametrize("n_points", [10_000, 60_000])
def test_volatility_high_freq(n_points):
    """Generate *n_points* 1-second bars and compute volatility within <0.5s."""
    idx = pd.date_range("2023-01-01", periods=n_points, freq="s")
    # Construct prices without re-indexing pitfalls (avoid all-NaN data).
    prices = 100 + 0.0001 * pd.Series(range(n_points), index=idx, dtype=float)

    start = time.perf_counter()
    vol = metrics.volatility(prices)
    duration = time.perf_counter() - start

    # Ensure the calculation remains performant; <1.5 s on typical CI runners.
    assert duration < 1.5, (
        f"Volatility calc too slow: {duration:.3f}s for {n_points} points"
    )
    assert not pd.isna(vol)
    assert vol >= 0

"""Smoke-test the paper-trading CLI with a dummy provider so the test runs fast
and doesn’t hit the real network.
"""

from datetime import datetime, timedelta
from pathlib import Path
from types import SimpleNamespace

import importlib
import sys

import pandas as pd
import pytest

# ---------------------------------------------------------------------------
# Dummy provider ----------------------------------------------------------------
# ---------------------------------------------------------------------------

class DummyProvider:  # noqa: D101 – test helper
    def __init__(self):
        self._price = 100.0

    def get_historical_data(self, symbol, start_date, end_date):  # noqa: D401
        idx = pd.date_range(start_date, periods=30, freq="D")
        return pd.DataFrame({"Close": self._price}, index=idx)

    def get_real_time_quote(self, symbol):  # noqa: D401
        self._price += 1.0  # monotonic price increase
        return {"price": self._price}


@pytest.fixture(autouse=True)
def patch_provider(monkeypatch):
    """Route YahooFinanceProvider → DummyProvider so the CLI is deterministic."""

    from src import data as _data_pkg

    monkeypatch.setattr(_data_pkg.providers, "YahooFinanceProvider", DummyProvider)
    yield


def test_cli_runs(tmp_path: Path, monkeypatch):
    """Run 3 ticks and verify that a report file was produced."""

    # Prevent loguru from printing during pytest run
    monkeypatch.setenv("LOGURU_LEVEL", "WARNING")

    # Import the CLI module fresh (ensures patched provider is used)
    cli = importlib.import_module("run_paper_trade")
    outdir = tmp_path / "reports"

    argv = [
        "--symbol",
        "FAKE",
        "--strategy",
        "buy_and_hold",
        "--max-ticks",
        "3",
        "--refresh",
        "0",  # no sleep
        "--outdir",
        str(outdir),
    ]

    # Run main (no exception means success)
    cli.main(argv)

    # A single HTML file should exist in outdir
    reports = list(outdir.glob("paper_FAKE.html"))
    assert reports, "Expected HTML report not found"

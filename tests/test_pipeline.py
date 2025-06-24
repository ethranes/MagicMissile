import asyncio
from datetime import date, datetime
from pathlib import Path

import pandas as pd
import pytest

from src.pipeline.data_pipeline import DataPipeline
from src.utils.validators import is_valid_symbol


class DummyProvider:
    def __init__(self):
        self.calls = 0

    def validate_symbol(self, symbol: str) -> bool:  # noqa: D401
        return is_valid_symbol(symbol)

    def get_historical_data(self, symbol, start_date, end_date):  # noqa: D401
        self.calls += 1
        idx = pd.date_range(start_date, end_date, freq="D")
        df = pd.DataFrame(
            {
                "Open": 1.0,
                "High": 1.0,
                "Low": 1.0,
                "Close": 1.0,
                "Volume": 100,
            },
            index=idx,
        )
        return df

    # Unused
    def get_real_time_quote(self, symbol):  # noqa: D401
        return {"price": 1.0}

    def get_multiple_quotes(self, symbols):  # noqa: D401
        return {s: {"price": 1.0} for s in symbols}


@pytest.mark.asyncio
async def test_pipeline_collect(monkeypatch, tmp_path: Path):
    # Patch DB to use in-memory sqlite
    from src.data.storage import database as db_module

    monkeypatch.setattr(db_module, "_DEFAULT_DB_PATH", tmp_path / "mem.db")

    provider = DummyProvider()
    pipeline = DataPipeline(provider, ["AAPL", "MSFT"], date(2022, 1, 1), date(2022, 1, 3))

    await pipeline.collect()

    assert provider.calls == 2

from datetime import datetime
from pathlib import Path

import pandas as pd
import pytest


class DummyTicker:
    def __init__(self, price: float):
        self.info = {"regularMarketPrice": price}


class DummyTickers:
    def __init__(self, mapping):
        self.tickers = {k: DummyTicker(v) for k, v in mapping.items()}


@pytest.fixture()
def sample_df():
    idx = pd.date_range("2022-01-01", periods=5, freq="D")
    df = pd.DataFrame({
        "Open": 1.0,
        "High": 1.0,
        "Low": 1.0,
        "Close": 1.0,
        "Volume": 100,
    }, index=idx)
    return df


@pytest.fixture()
def provider(tmp_path: Path):
    from src.data.providers.yahoo import YahooFinanceProvider

    return YahooFinanceProvider(cache=True, cache_dir=tmp_path)


def test_validate_symbol(provider):
    assert provider.validate_symbol("AAPL")
    assert not provider.validate_symbol("AAP$L")


def test_caching_and_quotes(monkeypatch, provider, sample_df):
    call_count = {"cnt": 0}

    def fake_download(ticker, start, end, progress):  # noqa: D401
        call_count["cnt"] += 1
        return sample_df

    monkeypatch.setattr("yfinance.download", fake_download)

    # Monkeypatch ticker classes
    monkeypatch.setattr("yfinance.Ticker", lambda symbol: DummyTicker(123.45))
    monkeypatch.setattr(
        "yfinance.Tickers",
        lambda symbols: DummyTickers({s: 200.0 for s in symbols.split()}),
    )

    start = datetime(2022, 1, 1)
    end = datetime(2022, 1, 5)

    # First call hits fake_download
    df1 = provider.get_historical_data("AAPL", start, end)
    assert not df1.empty
    assert call_count["cnt"] == 1

    # Second call should load from cache, not increase counter
    df2 = provider.get_historical_data("AAPL", start, end)
    assert call_count["cnt"] == 1
    assert df2.equals(df1)

    # Real-time quote
    quote = provider.get_real_time_quote("AAPL")
    assert quote["price"] == 123.45

    # Multiple quotes
    quotes = provider.get_multiple_quotes(["AAPL", "MSFT"])
    assert quotes["MSFT"]["price"] == 200.0

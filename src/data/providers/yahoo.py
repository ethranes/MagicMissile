from __future__ import annotations

from datetime import datetime
from typing import Dict, List

import pandas as pd
import yfinance as yf

import os
import pickle
import time
from pathlib import Path
import re

from ...core.exceptions import DataProviderError
from ...utils import is_valid_symbol
from .base import DataProvider


class YahooFinanceProvider(DataProvider):
    """Yahoo Finance data provider using yfinance library.

    Args:
        cache (bool): Enable file-based caching of historical data.
        cache_dir (str | Path): Directory to store cached files.
        min_interval (float): Minimum seconds between API calls (rate limiting).
    """

    def __init__(self, cache: bool = False, cache_dir: str | Path = "data/cache", min_interval: float = 1.0) -> None:
        self.cache = cache
        self.cache_dir = Path(cache_dir)
        if self.cache:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.min_interval = min_interval
        self._last_call_ts: float = 0.0

    # ------------------------ internal helpers ---------------------

    @staticmethod
    def _clean(df: pd.DataFrame) -> pd.DataFrame:
        """Basic cleaning: drop NaNs and ensure numeric columns."""

        df = df.dropna(how="any")
        return df

    def _rate_limit(self) -> None:
        now = time.time()
        elapsed = now - self._last_call_ts
        if elapsed < self.min_interval:
            time.sleep(self.min_interval - elapsed)
        self._last_call_ts = time.time()

    def _cache_path(self, ticker: str, start: datetime, end: datetime) -> Path:
        key = f"{ticker}_{start:%Y%m%d}_{end:%Y%m%d}.pkl"
        return self.cache_dir / key

    def _fetch(self, ticker: str, start: datetime, end: datetime) -> pd.DataFrame:
        # Try cache first
        if self.cache:
            pth = self._cache_path(ticker, start, end)
            if pth.is_file():
                with pth.open("rb") as f:
                    return pickle.load(f)

        # Rate limiting
        self._rate_limit()

        data = yf.download(ticker, start=start, end=end, progress=False)
        if data.empty:
            raise DataProviderError(f"No data returned for ticker: {ticker}")
        data.index.name = "date"
        data = self._clean(data)

        if self.cache:
            with self._cache_path(ticker, start, end).open("wb") as f:
                pickle.dump(data, f)
        return data

    def validate_symbol(self, symbol: str) -> bool:  # type: ignore[override]
        return is_valid_symbol(symbol)

    def get_historical_data(
        self, symbol: str, start_date: datetime, end_date: datetime
    ) -> pd.DataFrame:
        if not self.validate_symbol(symbol):
            raise DataProviderError(f"Invalid symbol: {symbol}")
        return self._fetch(symbol, start_date, end_date)

    def get_real_time_quote(self, symbol: str) -> Dict[str, float]:
        if not self.validate_symbol(symbol):
            raise DataProviderError(f"Invalid symbol: {symbol}")
        self._rate_limit()
        ticker = yf.Ticker(symbol)
        price = ticker.info.get("regularMarketPrice")
        if price is None:
            raise DataProviderError(f"Unable to fetch quote for {symbol}")
        return {"price": price}

    def get_multiple_quotes(self, symbols: List[str]) -> Dict[str, Dict[str, float]]:
        invalid = [s for s in symbols if not self.validate_symbol(s)]
        if invalid:
            raise DataProviderError(f"Invalid symbol(s): {', '.join(invalid)}")
        self._rate_limit()
        tickers = yf.Tickers(" ".join(symbols))
        quotes: Dict[str, Dict[str, float]] = {}
        for sym in symbols:
            price = tickers.tickers[sym].info.get("regularMarketPrice")
            if price is None:
                continue
            quotes[sym] = {"price": price}
        if not quotes:
            raise DataProviderError("No quotes retrieved for provided symbols")
        return quotes

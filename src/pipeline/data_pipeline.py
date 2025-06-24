from __future__ import annotations

import asyncio
import logging
from datetime import date, datetime
from typing import Iterable, List

import pandas as pd

from ..core.exceptions import DataProviderError
from ..core.logging_config import logger, log_timing, new_correlation_id
from ..data.providers.base import DataProvider
from ..data.storage import get_session, run_migrations
from ..data.storage.database import init_engine
from ..data.storage.repository import upsert_historical_df
from ..utils.transform import normalize_ohlcv


class DataPipeline:
    """Orchestrates data fetching, validation, transformation, and storage."""

    def __init__(
        self,
        provider: DataProvider,
        symbols: Iterable[str],
        start: date,
        end: date,
        *,
        max_concurrency: int = 5,
    ) -> None:
        self.provider = provider
        self.symbols: List[str] = list(symbols)
        self.start = start
        self.end = end
        self.semaphore = asyncio.Semaphore(max_concurrency)

        # Ensure DB initialized
        engine = init_engine()
        run_migrations(engine)

    # -------------------------------------------------------
    async def _fetch_symbol(self, symbol: str) -> tuple[str, pd.DataFrame | None]:
        """Fetch symbol data with quality checks; returns (symbol, df or None)."""

        async with self.semaphore:
            loop = asyncio.get_running_loop()
            try:
                df: pd.DataFrame = await loop.run_in_executor(
                    None,
                    self.provider.get_historical_data,
                    symbol,
                    datetime.combine(self.start, datetime.min.time()),
                    datetime.combine(self.end, datetime.min.time()),
                )
            except DataProviderError as exc:
                logger.error(f"Provider error for {symbol}: {exc}")
                return symbol, None
            except Exception as exc:  # noqa: BLE001
                logger.exception(f"Unexpected error fetching {symbol}: {exc}")
                return symbol, None

            # Data quality check
            if df.empty:
                logger.warning(f"No data for {symbol} between {self.start} and {self.end}")
                return symbol, None
            if df.isna().any().any():
                logger.warning(f"NaNs found in data for {symbol}; dropping")
                df = df.dropna()
            try:
                df = normalize_ohlcv(df)
            except ValueError as exc:
                logger.error(f"Data quality failure for {symbol}: {exc}")
                return symbol, None
            return symbol, df

    # -------------------------------------------------------
    @log_timing()
    async def collect(self) -> None:
        """Fetch and store data for all symbols (one-shot)."""

        cid = new_correlation_id()
        logger.info(f"Starting data collection cid={cid} for {len(self.symbols)} symbols")

        results = await asyncio.gather(*(self._fetch_symbol(s) for s in self.symbols))

        # Store
        with get_session() as sess:
            for symbol, df in results:
                if df is None:
                    continue
                upsert_historical_df(symbol, df, sess)
        logger.info("Data collection finished")

    # -------------------------------------------------------
    async def stream(self, interval_seconds: int = 3600) -> None:  # pragma: no cover
        """Continuously collect data at *interval_seconds* intervals."""

        while True:
            try:
                await self.collect()
            except Exception as exc:  # noqa: BLE001
                logger.exception(f"Pipeline iteration failed: {exc}")
            await asyncio.sleep(interval_seconds)

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, List

import pandas as pd


class DataProvider(ABC):
    """Abstract base class for market data providers."""

    @abstractmethod
    def get_historical_data(
        self, symbol: str, start_date: datetime, end_date: datetime
    ) -> pd.DataFrame:
        """Fetch historical OHLCV data for a single symbol."""

    @abstractmethod
    def get_real_time_quote(self, symbol: str) -> Dict[str, float]:
        """Fetch current quote for a single symbol."""

    @abstractmethod
    def get_multiple_quotes(self, symbols: List[str]) -> Dict[str, Dict[str, float]]:
        """Fetch current quotes for multiple symbols."""

    @abstractmethod
    def validate_symbol(self, symbol: str) -> bool:
        """Validate that the provided symbol conforms to provider rules."""

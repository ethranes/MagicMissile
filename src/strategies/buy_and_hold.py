from __future__ import annotations

from typing import Dict

import pandas as pd

from .base import Strategy
from .signal import Signal, SignalType


class BuyAndHoldStrategy(Strategy):
    """Simple buy-and-hold strategy.

    Buys at the first available close price and holds indefinitely.
    """

    name = "BuyAndHold"

    def generate_signals(self, data: pd.DataFrame) -> Dict[str, Signal]:
        if data.empty:
            return {}
        first_date = data.index.min()
        first_price = data.iloc[0]["Close"]
        signal = Signal(type=SignalType.BUY, confidence=1.0, metadata={"price": first_price, "date": first_date})
        return {"AAPL": signal}

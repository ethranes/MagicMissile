from __future__ import annotations

from typing import Dict

import pandas as pd
from pydantic import BaseModel, Field

from .base import Strategy
from .signal import Signal, SignalType


class BBParams(BaseModel):
    symbol: str = "AAPL"
    window: int = Field(20, ge=1)
    num_std: float = Field(2.0, ge=0.1)


class BollingerBandsStrategy(Strategy):
    """Bollinger Bands breakout strategy.

    BUY when price crosses below lower band (oversold), SELL when above upper band.
    """

    name = "BollingerBands"
    ParamModel = BBParams

    def generate_signals(self, data: pd.DataFrame) -> Dict[str, Signal]:  # noqa: D401
        if data.empty or "Close" not in data.columns:
            return {}
        p = BBParams(**self.parameters)  # type: ignore[arg-type]
        close = data["Close"].astype(float)
        ma = close.rolling(window=p.window).mean()
        std = close.rolling(window=p.window).std(ddof=0)
        upper = ma + p.num_std * std
        lower = ma - p.num_std * std
        if len(close) < p.window:
            return {}
        price = close.iloc[-1]
        up = upper.iloc[-1]
        lo = lower.iloc[-1]
        action = SignalType.HOLD
        if price < lo:
            action = SignalType.BUY
        elif price > up:
            action = SignalType.SELL
        sig = Signal(type=action, confidence=1.0, metadata={"price": price, "upper": up, "lower": lo})
        return {p.symbol: sig}

    def get_required_indicators(self):  # noqa: D401
        return ["Close"]

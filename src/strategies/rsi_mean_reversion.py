from __future__ import annotations

from typing import Dict

import pandas as pd
from pydantic import BaseModel, Field

from .base import Strategy
from .signal import Signal, SignalType


class RSIParams(BaseModel):
    symbol: str = "AAPL"
    window: int = Field(14, ge=1)
    oversold: int = Field(30, ge=1, le=50)
    overbought: int = Field(70, ge=50, le=99)


class RSIMeanReversionStrategy(Strategy):
    """RSI-based mean reversion strategy.

    BUY when RSI < oversold, SELL when RSI > overbought.
    """

    name = "RSIMeanReversion"
    ParamModel = RSIParams

    def _rsi(self, series: pd.Series, window: int) -> pd.Series:  # noqa: D401
        delta = series.diff()
        up = delta.clip(lower=0)
        down = -delta.clip(upper=0)
        roll_up = up.rolling(window=window).mean()
        roll_down = down.rolling(window=window).mean()
        rs = roll_up / roll_down
        return 100 - (100 / (1 + rs))

    def generate_signals(self, data: pd.DataFrame) -> Dict[str, Signal]:  # noqa: D401
        if data.empty or "Close" not in data.columns:
            return {}
        p = RSIParams(**self.parameters)  # type: ignore[arg-type]
        rsi_series = self._rsi(data["Close"].astype(float), p.window)
        if rsi_series.empty:
            return {}
        rsi_val = rsi_series.iloc[-1]
        action = SignalType.HOLD
        if rsi_val < p.oversold:
            action = SignalType.BUY
        elif rsi_val > p.overbought:
            action = SignalType.SELL
        sig = Signal(type=action, confidence=1.0, metadata={"rsi": rsi_val})
        return {p.symbol: sig}

    def get_required_indicators(self):  # noqa: D401
        return ["Close"]

from __future__ import annotations

from typing import Dict, Any

import pandas as pd
from pydantic import BaseModel, Field, model_validator

from .base import Strategy
from .signal import Signal, SignalType


class SMAParams(BaseModel):
    symbol: str = "AAPL"
    fast_window: int = Field(50, ge=1)
    slow_window: int = Field(200, ge=2)

    @model_validator(mode="after")
    def check_windows(self):  # noqa: D401
        if self.fast_window >= self.slow_window:
            raise ValueError("fast_window must be < slow_window")
        return self


class SMACrossoverStrategy(Strategy):
    """Simple Moving Average crossover strategy.

    Generates BUY when fast SMA crosses above slow SMA; SELL on bearish cross.
    """

    name = "SMACrossover"
    ParamModel = SMAParams

    def generate_signals(self, data: pd.DataFrame) -> Dict[str, Signal]:  # noqa: D401
        if data.empty or "Close" not in data.columns:
            return {}
        p = SMAParams(**self.parameters)  # type: ignore[arg-type]
        close = data["Close"].astype(float)
        fast = close.rolling(window=p.fast_window).mean()
        slow = close.rolling(window=p.slow_window).mean()
        # need two points to determine cross
        if len(close) < p.slow_window + 1:
            return {}
        fast_curr, fast_prev = fast.iloc[-1], fast.iloc[-2]
        slow_curr, slow_prev = slow.iloc[-1], slow.iloc[-2]
        action: SignalType = SignalType.HOLD
        if fast_prev <= slow_prev and fast_curr > slow_curr:
            action = SignalType.BUY
        elif fast_prev >= slow_prev and fast_curr < slow_curr:
            action = SignalType.SELL
        sig = Signal(type=action, confidence=1.0)
        return {p.symbol: sig}

    def get_required_indicators(self):  # noqa: D401
        return ["Close"]

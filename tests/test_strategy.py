import pandas as pd
import pytest

from src.strategies.buy_and_hold import BuyAndHoldStrategy
from src.strategies.signal import SignalType


def test_buy_and_hold_signal():
    strat = BuyAndHoldStrategy()
    idx = pd.date_range("2022-01-01", periods=2, freq="D")
    df = pd.DataFrame({"Close": [100, 101]}, index=idx)
    signals = strat.generate_signals(df)
    assert "AAPL" in signals
    sig = signals["AAPL"]
    assert sig.type == SignalType.BUY
    assert sig.confidence == 1.0

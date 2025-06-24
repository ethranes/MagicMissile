import pandas as pd

from src.strategies.sma_crossover import SMACrossoverStrategy
from src.strategies.rsi_mean_reversion import RSIMeanReversionStrategy
from src.strategies.bollinger_bands import BollingerBandsStrategy
from src.strategies.signal import SignalType


def _dummy_df():
    idx = pd.date_range("2022-01-01", periods=250, freq="D")
    prices = pd.Series(range(100, 350), index=idx, dtype=float)
    return pd.DataFrame({"Close": prices})


def test_sma_crossover():
    df = _dummy_df()
    strat = SMACrossoverStrategy({"symbol": "AAPL", "fast_window": 5, "slow_window": 10})
    sigs = strat.generate_signals(df)
    assert "AAPL" in sigs
    assert sigs["AAPL"].type in {SignalType.BUY, SignalType.SELL, SignalType.HOLD}


def test_rsi_strategy():
    df = _dummy_df()
    strat = RSIMeanReversionStrategy({"symbol": "AAPL", "window": 14})
    sigs = strat.generate_signals(df)
    assert "AAPL" in sigs


def test_bb_strategy():
    df = _dummy_df()
    strat = BollingerBandsStrategy({"symbol": "AAPL", "window": 20})
    sigs = strat.generate_signals(df)
    assert "AAPL" in sigs

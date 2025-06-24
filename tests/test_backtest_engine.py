import pandas as pd

from src.backtesting.engine import BacktestEngine
from src.strategies.buy_and_hold import BuyAndHoldStrategy


def _dummy_data():
    idx = pd.date_range("2022-01-01", periods=30, freq="D")
    prices = pd.Series(range(100, 130), index=idx, dtype=float)
    return {"AAPL": pd.DataFrame({"Close": prices})}


def test_backtest_runs():
    engine = BacktestEngine(_dummy_data(), [BuyAndHoldStrategy()], starting_cash=10000)
    equity = engine.run()
    # Ensure equity curve produced and final equity reasonable
    assert not equity.empty
    assert equity.iloc[-1]["equity"] >= 0

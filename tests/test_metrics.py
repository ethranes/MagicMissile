import math
from datetime import datetime, timedelta

import pandas as pd

from src.backtesting import metrics
from src.backtesting.events import FillEvent
from src.strategies.signal import SignalType


def test_metric_functions_basic_equity_curve():
    """Verify metric calculations on a simple equity curve."""
    idx = pd.date_range("2023-01-01", periods=5, freq="D")
    equity = pd.Series([100, 102, 101, 104, 108], index=idx)

    assert math.isclose(metrics.total_return(equity), 0.08, rel_tol=1e-9)
    # Annualized roughly ((1+0.08) ** (252/4) - 1). Just check it's positive
    assert metrics.annualized_return(equity) > 0
    assert metrics.volatility(equity) > 0
    assert not math.isnan(metrics.sharpe_ratio(equity))
    max_dd, dur = metrics.max_drawdown(equity)
    assert max_dd < 0  # drawdown negative
    assert dur >= 0


def test_trade_based_metrics():
    """Verify win/loss ratio and average trade duration calculations."""
    t0 = datetime(2023, 1, 1)
    trades = [
        FillEvent("AAPL", t0, SignalType.BUY, 10, 100),
        FillEvent("AAPL", t0 + timedelta(days=3), SignalType.SELL, 10, 105),  # +5
        FillEvent("AAPL", t0 + timedelta(days=4), SignalType.BUY, 10, 106),
        FillEvent("AAPL", t0 + timedelta(days=6), SignalType.SELL, 10, 103),  # -3
    ]

    wl_ratio = metrics.win_loss_ratio(trades)
    assert math.isclose(wl_ratio, 0.5, rel_tol=1e-9)

    avg_dur = metrics.average_trade_duration(trades)
    assert math.isclose(avg_dur, 2.5, rel_tol=1e-9)


def test_calmar_and_rolling():
    idx = pd.date_range("2023-01-01", periods=252, freq="B")
    # equity grows linearly 0.1% per day
    equity = pd.Series(100 * (1 + 0.001) ** pd.Series(range(len(idx))), index=idx)
    # Calmar ratio should be NaN because max drawdown is zero
    assert math.isnan(metrics.calmar_ratio(equity))
    roll_sharpe = metrics.rolling_sharpe_ratio(equity, window=20)
    # Rolling series must align and have NaNs for first window-1 entries
    assert roll_sharpe.isna()[:19].all()
    assert (roll_sharpe[20:] > 0).all()


def test_summary():
    idx = pd.date_range("2023-01-01", periods=5, freq="D")
    equity = pd.Series([100, 102, 101, 104, 108], index=idx)
    summary = metrics.summary(equity)
    assert summary.total_return == metrics.total_return(equity)
    assert summary.win_loss_ratio is None  # trades not supplied
    # Ensure calmar present
    assert summary.calmar_ratio == metrics.calmar_ratio(equity)


def test_performance_report():
    idx = pd.date_range("2023-01-01", periods=5, freq="D")
    equity = pd.Series([100, 101, 103, 102, 105], index=idx)
    df = metrics.performance_report(equity)
    assert df.shape == (1, len(df.columns))
    assert "total_return" in df.columns

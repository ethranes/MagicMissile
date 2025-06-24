from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Dict, Optional, List

from src.backtesting.events import FillEvent
from src.strategies.signal import SignalType

import numpy as np
import pandas as pd

TRADING_DAYS = 252


@dataclass(slots=True)
class PerformanceSummary:
    total_return: float
    annualized_return: float
    sharpe_ratio: float
    sortino_ratio: float
    max_drawdown: float
    max_drawdown_duration: int
    volatility: float
    calmar_ratio: Optional[float] = None
    win_loss_ratio: Optional[float] = None
    avg_trade_duration: Optional[float] = None  # days
    beta: Optional[float] = None


# ---------------------------------------------------------------------------

def _returns(equity: pd.Series) -> pd.Series:  # noqa: D401
    ret = equity.pct_change().dropna()
    return ret


# ---------------------------------------------------------------------------

def total_return(equity: pd.Series) -> float:  # noqa: D401
    return equity.iloc[-1] / equity.iloc[0] - 1


def annualized_return(equity: pd.Series) -> float:  # noqa: D401
    n = equity.shape[0]
    return (equity.iloc[-1] / equity.iloc[0]) ** (TRADING_DAYS / n) - 1


def volatility(equity: pd.Series) -> float:  # noqa: D401
    ret = _returns(equity)
    return ret.std(ddof=0) * np.sqrt(TRADING_DAYS)


def sharpe_ratio(equity: pd.Series, risk_free: float = 0.0) -> float:  # noqa: D401
    ret = _returns(equity) - risk_free / TRADING_DAYS
    if ret.std(ddof=0) == 0:
        return np.nan
    return np.sqrt(TRADING_DAYS) * ret.mean() / ret.std(ddof=0)


def sortino_ratio(equity: pd.Series, risk_free: float = 0.0) -> float:  # noqa: D401
    ret = _returns(equity) - risk_free / TRADING_DAYS
    downside = ret[ret < 0]
    denom = downside.std(ddof=0)
    if denom == 0:
        return np.nan
    return np.sqrt(TRADING_DAYS) * ret.mean() / denom


def max_drawdown(equity: pd.Series) -> tuple[float, int]:  # noqa: D401
    roll_max = equity.cummax()
    drawdown = equity / roll_max - 1.0
    max_dd = drawdown.min()
    # duration
    trough_idx = drawdown.idxmin()
    post_trough = equity.loc[trough_idx:]
    recovery_idx = post_trough[post_trough >= roll_max.loc[trough_idx]].first_valid_index()
    if recovery_idx is None:
        duration = len(equity) - equity.index.get_loc(trough_idx)
    else:
        duration = equity.index.get_loc(recovery_idx) - equity.index.get_loc(trough_idx)
    return float(max_dd), int(duration)


def beta_vs_benchmark(equity: pd.Series, benchmark: pd.Series) -> float:  # noqa: D401
    ret = _returns(equity)
    bench_ret = _returns(benchmark)
    aligned = pd.concat([ret, bench_ret], axis=1, join="inner").dropna()
    if aligned.empty:
        return np.nan
    cov = np.cov(aligned.iloc[:, 0], aligned.iloc[:, 1])[0, 1]
    var = aligned.iloc[:, 1].var(ddof=0)
    if var == 0:
        return np.nan
    return cov / var


# ---------------------------------------------------------------------------


def win_loss_ratio(trades: List[FillEvent] | None) -> float:
    """Win/loss ratio for round-trip trades.

    Returns NaN if no closed trades.
    """
    if not trades:
        return np.nan
    wins = 0
    losses = 0
    open_pos: Dict[str, FillEvent] = {}
    for fill in trades:
        if fill.fill_type == SignalType.BUY:
            open_pos[fill.symbol] = fill
        elif fill.fill_type == SignalType.SELL and fill.symbol in open_pos:
            entry = open_pos.pop(fill.symbol)
            pnl = (fill.price - entry.price) * entry.quantity
            if pnl > 0:
                wins += 1
            else:
                losses += 1
    total = wins + losses
    return np.nan if total == 0 else wins / total


def average_trade_duration(trades: List[FillEvent] | None) -> float:
    """Average holding period (days) between buy and sell fills."""
    if not trades:
        return np.nan
    durations: List[int] = []
    open_pos: Dict[str, FillEvent] = {}
    for fill in trades:
        if fill.fill_type == SignalType.BUY:
            open_pos[fill.symbol] = fill
        elif fill.fill_type == SignalType.SELL and fill.symbol in open_pos:
            entry = open_pos.pop(fill.symbol)
            durations.append((fill.time - entry.time).days)
    return np.nan if not durations else float(np.mean(durations))

# ---------------------------------------------------------------------------


def calmar_ratio(equity: pd.Series) -> float:  # noqa: D401
    """Calmar ratio: annualized return divided by absolute max drawdown."""
    ret = annualized_return(equity)
    dd = equity / equity.cummax() - 1.0
    max_dd = dd.min()
    if max_dd == 0:
        return np.nan
    return ret / abs(max_dd)


def rolling_sharpe_ratio(
    equity: pd.Series, window: int = 126, risk_free: float = 0.0
) -> pd.Series:  # noqa: D401
    """Compute rolling Sharpe ratio using a lookback window (default ~6 months)."""
    returns = _returns(equity) - risk_free / TRADING_DAYS
    def _sharpe(x):
        sd = x.std(ddof=0)
        return np.nan if sd == 0 else np.sqrt(TRADING_DAYS) * x.mean() / sd
    return returns.rolling(window=window).apply(_sharpe, raw=False)


def performance_report(
    equity: pd.Series,
    benchmark: Optional[pd.Series] = None,
    trades: Optional[List[FillEvent]] = None,
) -> pd.DataFrame:  # noqa: D401
    """Return a one-row DataFrame of the performance summary."""
    summ = summary(equity, benchmark, trades)
    return pd.DataFrame([asdict(summ)])

# ---------------------------------------------------------------------------

def summary(equity: pd.Series, benchmark: Optional[pd.Series] = None, trades: Optional[List[FillEvent]] = None) -> PerformanceSummary:  # noqa: D401
    max_dd, dd_duration = max_drawdown(equity)
    beta = beta_vs_benchmark(equity, benchmark) if benchmark is not None else None
    return PerformanceSummary(
        total_return=total_return(equity),
        annualized_return=annualized_return(equity),
        sharpe_ratio=sharpe_ratio(equity),
        sortino_ratio=sortino_ratio(equity),
        max_drawdown=max_dd,
        max_drawdown_duration=dd_duration,
        volatility=volatility(equity),
        calmar_ratio=calmar_ratio(equity),
        win_loss_ratio=win_loss_ratio(trades) if trades is not None else None,
        avg_trade_duration=average_trade_duration(trades) if trades is not None else None,
        beta=beta,
    )

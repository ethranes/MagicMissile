from __future__ import annotations

from dataclasses import dataclass
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
        win_loss_ratio=win_loss_ratio(trades) if trades is not None else None,
        avg_trade_duration=average_trade_duration(trades) if trades is not None else None,
        beta=beta,
    )

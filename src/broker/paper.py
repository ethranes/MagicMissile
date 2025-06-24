from __future__ import annotations

"""Paper trading broker that simulates live execution using historical/real-time
price ticks.  Supports latency, slippage, and leverages the existing
``OrderBook`` + ``PortfolioManager`` infrastructure.
"""

from collections import deque
from datetime import datetime, timedelta
from typing import Deque, Dict, List, Tuple, Union

from pathlib import Path
from src.backtesting.events import FillEvent
from src.orders.order import Order
from src.orders.order_book import OrderBook
from src.portfolio.manager import PortfolioManager
from src.strategies.signal import SignalType

import pandas as pd
from src.backtesting.metrics import summary
from src.backtesting.report import generate_html_report

__all__ = ["PaperBroker"]


class PaperBroker:
    """Simulated broker for live/paper trading.

    A very lightweight wrapper around :class:`~src.orders.order_book.OrderBook`
    that introduces *latency* and *slippage* while keeping positions in a
    :class:`~src.portfolio.manager.PortfolioManager`.
    """

    def __init__(
        self,
        *,
        starting_cash: float = 100_000.0,
        latency: timedelta = timedelta(seconds=0),
        slippage_pct: float = 0.0005,
        max_qty_per_fill: int | None = None,
    ) -> None:
        self.latency = latency
        self.slippage_pct = slippage_pct
        self._delay_queue: Deque[Tuple[datetime, Order]] = deque()
        self.order_book = OrderBook(max_qty_per_fill=max_qty_per_fill)
        self.portfolio = PortfolioManager(starting_cash)
        self.fills: List[FillEvent] = []
        self._equity_curve: List[Tuple[datetime, float]] = []
        self._last_prices: Dict[str, float] = {}

    # ---------------------------------------------------------------------
    # Order submission ------------------------------------------------------
    def submit_order(self, order: Order, now: datetime | None = None) -> None:
        """Queue *order* for execution.  It will enter the book after *latency*."""

        ts = now or datetime.utcnow()
        ready_ts = ts + self.latency
        self._delay_queue.append((ready_ts, order))

    def cancel_order(self, order_id: str) -> bool:
        # Try pending queue first
        for idx, (_, o) in enumerate(self._delay_queue):
            if o.id == order_id:
                del self._delay_queue[idx]
                return True
        # Else active book
        return self.order_book.cancel_order(order_id)

    # ---------------------------------------------------------------------
    # Market data processing ------------------------------------------------
    def on_price_tick(
        self,
        symbol: str,
        time: datetime,
        price: float,
        high: float,
        low: float,
        *,
        commission: float = 0.0,
    ) -> List[FillEvent]:
        """Process a price tick (OHLC).  Returns list of *new* fills."""

        # Track last prices
        self._last_prices[symbol] = price

        # Flush any queued orders that have cleared latency window
        while self._delay_queue and self._delay_queue[0][0] <= time:
            _, order = self._delay_queue.popleft()
            self.order_book.add_order(order)

        # Let the order-book attempt fills for this bar
        fills = self.order_book.process_bar(
            symbol,
            time,
            price,
            high,
            low,
            commission=commission,
        )

        # Apply slippage then update portfolio
        for f in fills:
            if self.slippage_pct:
                if f.fill_type == SignalType.BUY:
                    f.price *= 1 + self.slippage_pct
                else:
                    f.price *= 1 - self.slippage_pct
            self.portfolio.apply_fill(f)
        if fills:
            self.fills.extend(fills)

        # Record equity after processing this bar
        equity = self.portfolio.total_equity(self._last_prices)
        self._equity_curve.append((time, equity))
        return fills

    # ---------------------------------------------------------------------
    # Reporting / control ---------------------------------------------------
    def equity(self, prices: Dict[str, float]) -> float:  # noqa: D401
        """Current equity including mark-to-market of open positions."""

        return self.portfolio.total_equity(prices)

    # ---------------------------------------------------------------------
    # Performance report ----------------------------------------------------
    def generate_performance_report(self, output_path: Union[str, Path]) -> Path:
        """Generate an interactive HTML performance report.

        Args:
            output_path: Filepath where the report will be written (``.html``).

        Returns:
            Path to the generated HTML file.
        """
        if not self._equity_curve:
            raise ValueError("No equity data recorded – run on_price_tick first")
        times, equities = zip(*self._equity_curve)
        series = pd.Series(equities, index=pd.to_datetime(times), name="equity")
        perf_summary = summary(series)
        return generate_html_report(series, perf_summary, output_path, trades=self.fills)

    def reset(self) -> None:
        """Reset internal state (orders, fills, cash/positions)."""

        self._delay_queue.clear()
        self.order_book = OrderBook(self.order_book._max_qty_per_fill)
        self.portfolio = PortfolioManager(self.portfolio.cash + self.portfolio.margin_used)
        self.fills.clear()

    # Convenience -----------------------------------------------------------
    def pending_orders(self) -> List[Order]:  # noqa: D401
        return [o for _, o in self._delay_queue] + [
            o for lst in self.order_book._orders.values() for o in lst if o.is_open()
        ]

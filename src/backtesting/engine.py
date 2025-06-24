from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Sequence

import pandas as pd

from src.strategies.base import Strategy
from src.strategies.signal import SignalType

from src.orders.order import Order
from src.orders.order_book import OrderBook
from src.orders.types import OrderType
from src.portfolio.manager import PortfolioManager

from .events import FillEvent, MarketEvent, SignalEvent


@dataclass
class Position:
    quantity: int = 0
    avg_price: float = 0.0


class Portfolio:
    """Tracks cash, positions, equity, and transactions."""

    def __init__(self, starting_cash: float) -> None:
        self.cash = starting_cash
        self.positions: Dict[str, Position] = defaultdict(Position)
        self.trades: List[FillEvent] = []

    # -------------------------------------------------------------
    def update_with_fill(self, fill: FillEvent) -> None:
        pos = self.positions[fill.symbol]
        direction = 1 if fill.fill_type == SignalType.BUY else -1
        new_qty = pos.quantity + direction * fill.quantity
        if new_qty == 0:
            pos.avg_price = 0.0
        else:
            # weighted average price
            pos.avg_price = (
                (pos.avg_price * abs(pos.quantity) + fill.price * fill.quantity) / abs(new_qty)
            )
        pos.quantity = new_qty
        cost = fill.price * fill.quantity + fill.commission
        self.cash -= direction * cost  # BUY decreases cash, SELL increases cash
        self.trades.append(fill)

    # -------------------------------------------------------------
    def market_value(self, prices: Dict[str, float]) -> float:
        mv = sum(pos.quantity * prices.get(sym, 0.0) for sym, pos in self.positions.items())
        return mv

    def total_equity(self, prices: Dict[str, float]) -> float:
        return self.cash + self.market_value(prices)


class BacktestEngine:
    """Event-driven backtesting engine supporting multiple strategies."""

    def __init__(
        self,
        data: Dict[str, pd.DataFrame],
        strategies: Sequence[Strategy],
        *,
        starting_cash: float = 100_000.0,
        commission: float = 1.0,
        slippage_pct: float = 0.0005,
        progress_interval: int = 100,
    ) -> None:
        # Align dates across symbols by outer join index
        self.data = data
        self.symbols = list(data.keys())
        self.dates = sorted(
            set().union(*[df.index.to_pydatetime().tolist() for df in data.values()])
        )
        self.strategies = strategies
        self.portfolio = PortfolioManager(starting_cash)
        self.commission = commission
        self.slippage_pct = slippage_pct
        self.progress_interval = progress_interval
        # Use new order-book for tracking and matching orders
        self.order_book = OrderBook()

    # ------------------------------------------------------------------
    def _price_at(self, symbol: str, time: datetime) -> float | None:
        df = self.data[symbol]
        if time in df.index:
            return float(df.loc[time]["Close"])
        return None

    # ------------------------------------------------------------------
    def _generate_market_events(self, time: datetime) -> List[MarketEvent]:
        events: List[MarketEvent] = []
        for sym in self.symbols:
            price = self._price_at(sym, time)
            if price is None:
                continue
            row = self.data[sym].loc[time].to_dict()
            events.append(MarketEvent(sym, time, price, row))
        return events

    # ------------------------------------------------------------------
    def _process_signals(self, time: datetime, signals: Dict[str, SignalEvent]) -> None:
        for sig in signals.values():
            if sig.signal_type == SignalType.HOLD:
                continue
            order = Order(
                symbol=sig.symbol,
                side=sig.signal_type,
                order_type=OrderType.MARKET,
                quantity=100,  # fixed lot for demo
            )
            self.order_book.add_order(order)

    # ------------------------------------------------------------------
    def _execute_orders(self, time: datetime) -> None:
        for sym in self.symbols:
            if time not in self.data[sym].index:
                continue
            row = self.data[sym].loc[time]
            # Handle datasets that may only contain Close values
            close = float(row["Close"])
            high = float(row.get("High", close))
            low = float(row.get("Low", close))

            fills = self.order_book.process_bar(
                sym,
                time,
                price=close,
                high=high,
                low=low,
                commission=self.commission,
            )
            for fill in fills:
                self.portfolio.update_with_fill(fill)

    # ------------------------------------------------------------------
    def run(self) -> pd.DataFrame:
        """Run backtest; returns equity curve DataFrame."""

        equity_curve = []
        for idx, dt in enumerate(self.dates):
            # 1. market events
            market_events = self._generate_market_events(dt)
            if not market_events:
                continue
            # 2. strategy signals
            for strat in self.strategies:
                # build dataframe subset for required indicators up to current time
                required_syms = {strat.parameters.get("symbol", sym) for sym in self.symbols}
                for sym in required_syms:
                    df = self.data[sym].loc[:dt]
                    sigs = strat.generate_signals(df)
                    if sym in sigs:
                        se = sigs[sym]
                        signal_event = SignalEvent(sym, dt, se.type, se.confidence)
                        self._process_signals(dt, {sym: signal_event})
            # 3. execute orders
            self._execute_orders(dt)
            # 4. record equity
            prices_now = {sym: self._price_at(sym, dt) or 0.0 for sym in self.symbols}
            equity = self.portfolio.total_equity(prices_now)
            equity_curve.append({"time": dt, "equity": equity})
            # 5. progress
            if (idx + 1) % self.progress_interval == 0:
                print(f"Progress: {idx+1}/{len(self.dates)}")
        return pd.DataFrame(equity_curve).set_index("time")

from __future__ import annotations

"""Portfolio management subsystem.

Tracks cash, positions, calculates real-time metrics and provides helper
utilities for sizing, rebalancing and risk monitoring.
"""

from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, MutableMapping

import json

from src.backtesting.events import FillEvent
from src.strategies.signal import SignalType


@dataclass(slots=True)
class Position:
    """Represents an open position in a single symbol."""

    quantity: int = 0
    avg_price: float = 0.0  # volume-weighted average cost

    def market_value(self, price: float) -> float:  # noqa: D401
        return self.quantity * price

    def unrealised_pnl(self, price: float) -> float:  # noqa: D401
        return (price - self.avg_price) * self.quantity


class PortfolioManager:
    """Keeps track of cash, positions and P&L in real time."""

    def __init__(
        self,
        starting_cash: float = 100_000.0,
        *,
        max_leverage: float = 2.0,
    ) -> None:  # noqa: D401
        """Create a portfolio manager.

        Args:
            starting_cash: Initial cash balance.
            max_leverage: Maximum allowable leverage (equity / net_liquidation).
                E.g. 2.0 means cash can go negative up to the value of equity.
        """
        self.cash: float = starting_cash
        self.max_leverage = max_leverage
        self._positions: MutableMapping[str, Position] = {}
        self.trade_history: List[FillEvent] = []
        self._equity_history: List[tuple[datetime, float]] = []  # (time, equity)

    # ------------------------------------------------------------------
    @property
    def positions(self) -> Dict[str, Position]:  # noqa: D401
        return dict(self._positions)

    # ------------------------------------------------------------------
    def apply_fill(self, fill: FillEvent) -> None:
        """Update portfolio state with an executed trade (FillEvent)."""

        pos = self._positions.setdefault(fill.symbol, Position())
        direction = 1 if fill.fill_type == SignalType.BUY else -1
        new_qty = pos.quantity + direction * fill.quantity

        if new_qty == 0:
            pos.avg_price = 0.0
        else:
            pos.avg_price = (
                (pos.avg_price * abs(pos.quantity) + fill.price * fill.quantity) / abs(new_qty)
            )
        pos.quantity = new_qty

        trade_cost = fill.price * fill.quantity + fill.commission
        self.cash -= direction * trade_cost  # BUY decreases cash, SELL increases cash
        self.trade_history.append(fill)

    # Backward-compat alias
    def update_with_fill(self, fill: FillEvent) -> None:  # noqa: D401
        self.apply_fill(fill)

    # ------------------------------------------------------------------
    # ------------------------------------------------------------------
    # Cash / margin helpers ----------------------------------------------
    @property
    def margin_used(self) -> float:  # noqa: D401
        """Current margin loan (positive number)."""
        return max(-self.cash, 0.0)

    def margin_limit(self, equity: float) -> float:  # noqa: D401
        """Maximum allowable margin given *equity* and leverage."""
        return max(equity * (self.max_leverage - 1.0), 0.0)

    # ------------------------------------------------------------------
    def market_value(self, prices: Dict[str, float]) -> float:
        return sum(pos.market_value(prices.get(sym, 0.0)) for sym, pos in self._positions.items())

    def unrealised_pnl(self, prices: Dict[str, float]) -> float:  # noqa: D401
        return sum(pos.unrealised_pnl(prices.get(sym, 0.0)) for sym, pos in self._positions.items())

    def total_equity(self, prices: Dict[str, float]) -> float:  # noqa: D401
        return self.cash + self.market_value(prices)

    # ------------------------------------------------------------------
    # Position sizing helpers -------------------------------------------------
    def size_for_risk(self, price: float, cash_risk_pct: float) -> int:
        """Return position size given risk % of current cash.

        Example: with 100k cash, `cash_risk_pct=0.02` at $50/share → 40 shares.
        """

        risk_dollars = self.cash * cash_risk_pct
        if price <= 0:
            return 0
        return int(risk_dollars // price)

    # ------------------------------------------------------------------
    def rebalance_to_target_weights(
        self, target_weights: Dict[str, float], prices: Dict[str, float]
    ) -> Dict[str, int]:
        """Return quantity diffs required to reach *target_weights*.

        Output maps symbol → delta quantity (positive = buy, negative = sell).
        """

        equity = self.total_equity(prices)
        deltas: Dict[str, int] = {}
        for sym, target_w in target_weights.items():
            target_dollars = equity * target_w
            current_qty = self._positions.get(sym, Position()).quantity
            current_dollars = current_qty * prices.get(sym, 0.0)
            diff_qty = int((target_dollars - current_dollars) // prices.get(sym, 1.0))
            if diff_qty != 0:
                deltas[sym] = diff_qty
        return deltas

    # ------------------------------------------------------------------
    # Simple risk monitoring --------------------------------------------------
    def check_drawdown(self, prices: Dict[str, float], threshold_pct: float) -> bool:
        """Return True if drawdown exceeds *threshold_pct* of peak equity."""

        equity = self.total_equity(prices)
        self._equity_history.append((datetime.utcnow(), equity))
        peak = max(e for _, e in self._equity_history)
        drawdown = (peak - equity) / peak if peak else 0.0
        return drawdown >= threshold_pct

    # ------------------------------------------------------------------
    # Persistence -------------------------------------------------------------
    def save(self, path: Path) -> None:  # noqa: D401
        data = {
            "cash": self.cash,
            "positions": {
                sym: {"qty": pos.quantity, "avg_price": pos.avg_price}
                for sym, pos in self._positions.items()
            },
            "trades": [dict(asdict(fill), time=fill.time.isoformat()) for fill in self.trade_history],
        }
        path.write_text(json.dumps(data, indent=2))

    @classmethod
    def load(cls, path: Path) -> "PortfolioManager":  # noqa: D401
        obj = cls()
        data = json.loads(path.read_text())
        obj.cash = data["cash"]
        for sym, info in data["positions"].items():
            obj._positions[sym] = Position(info["qty"], info["avg_price"])
        # trade history not reconstructed for brevity
        return obj

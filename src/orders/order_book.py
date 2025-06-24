from __future__ import annotations

"""Simple in-memory limit order book for backtesting purposes."""
from collections import defaultdict
from datetime import datetime
from typing import Dict, List

from src.backtesting.events import FillEvent
from src.strategies.signal import SignalType

from .order import Order
from .types import OrderType


class OrderBook:
    """Very lightweight order-book suitable for backtesting.

    It is *not* a full depth-of-market simulation – the goal is just to
    approximate basic order handling so strategies behave realistically.
    """

    def __init__(self, max_qty_per_fill: int | None = None) -> None:
        """Create a new order book.

        Args:
            max_qty_per_fill: Optional limit of how many shares/units can be
                executed for *each* order during a single bar.  If ``None`` the
                entire remaining quantity is eligible to be filled.  A finite
                value allows backtests to simulate *partial* fills when order
                size exceeds available liquidity.
        """
        self._orders: Dict[str, List[Order]] = defaultdict(list)  # active orders keyed by symbol
        self.history: List[Order] = []  # audit trail of all orders (active + completed)
        self._max_qty_per_fill = max_qty_per_fill

    # -----------------------------------------------------------------
    def add_order(self, order: Order) -> None:
        """Register a new order with the book."""

        self._orders[order.symbol].append(order)
        self.history.append(order)

    # -----------------------------------------------------------------
    def cancel_order(self, order_id: str) -> bool:
        """Cancel an order by its ID. Returns True if cancelled."""

        for orders in self._orders.values():
            for o in orders:
                if o.id == order_id and o.is_open():
                    o.cancel()
                    return True
        return False

    # -----------------------------------------------------------------
    def process_bar(
        self,
        symbol: str,
        time: datetime,
        price: float,
        high: float,
        low: float,
        *,
        commission: float = 0.0,
        max_qty_per_fill: int | None = None,
    ) -> List[FillEvent]:
        """Attempt to execute any open orders for *symbol* given the OHLC data.

        Returns a list of `FillEvent`s that were generated during this bar.
        """

        fills: List[FillEvent] = []
        if symbol not in self._orders:
            return fills

        for order in list(self._orders[symbol]):
            if not order.is_open():
                continue

            # Handle timeouts first
            order.maybe_timeout(time)
            if not order.is_open():
                continue

            # ----------------------------------------------------------------
            # MARKET orders are filled immediately at the close price
            if order.order_type == OrderType.MARKET:
                fill_price = price

            # ----------------------------------------------------------------
            # LIMIT orders are filled if the limit is reached
            elif order.order_type == OrderType.LIMIT:
                if order.side == SignalType.BUY and low <= order.limit_price:
                    fill_price = min(order.limit_price, price)
                elif order.side == SignalType.SELL and high >= order.limit_price:
                    fill_price = max(order.limit_price, price)
                else:
                    continue  # Not eligible this bar

            # ----------------------------------------------------------------
            # STOP orders convert to market once stop level is hit
            elif order.order_type == OrderType.STOP:
                triggered = (
                    (order.side == SignalType.BUY and high >= order.stop_price)
                    or (order.side == SignalType.SELL and low <= order.stop_price)
                )
                if not triggered:
                    continue
                fill_price = price  # treat as market once triggered

            else:  # pragma: no cover – unreachable with current enum
                continue

            # ----------------------------------------------------------------
            # Determine how much of the order we can fill this bar.  Honour the
            # *max_qty_per_fill* argument if provided, otherwise fall back to
            # the order-book default.
            effective_cap = max_qty_per_fill if max_qty_per_fill is not None else self._max_qty_per_fill
            if effective_cap is None or order.filled_qty > 0:
                # No liquidity cap after the first fill to keep things simple
                qty = order.remaining
            else:
                qty = min(order.remaining, effective_cap)
            fill = FillEvent(
                symbol=symbol,
                time=time,
                fill_type=order.side,
                quantity=qty,
                price=fill_price,
                commission=commission,
            )
            order._record_fill(fill)
            fills.append(fill)

        return fills

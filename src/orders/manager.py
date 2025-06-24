from __future__ import annotations

"""Order manager responsible for validation and routing of orders to the chosen destination.

For backtesting the destination is an in-memory :class:`orders.order_book.OrderBook`.
In live trading this class can be extended to forward orders to a broker API.
"""

from src.core.exceptions import ExecutionError  # noqa: WPS433 – project-local import

from .order import Order
from .order_book import OrderBook


class OrderManager:  # pragma: no cover – simple wrapper, mostly exercised indirectly
    """Validate incoming orders and route them to the order book."""

    def __init__(self, order_book: OrderBook) -> None:
        self.order_book = order_book

    # -----------------------------------------------------------------
    def submit(self, order: Order) -> None:
        """Validate and submit an *order* to the book."""

        self._validate(order)
        self.order_book.add_order(order)

    # -----------------------------------------------------------------
    def _validate(self, order: Order) -> None:
        """Additional project-level business rules.

        Raises:
            ExecutionError: if any rule is violated.
        """

        # Quantity sanity check (should be positive and a multiple of 1 share)
        if order.quantity <= 0:
            raise ExecutionError("Order quantity must be positive")
        # Further validation rules can be added here (e.g. max order size).

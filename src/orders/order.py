from __future__ import annotations

"""Core order object used by the order-management system."""
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import List, Optional
from uuid import uuid4

from src.backtesting.events import FillEvent
from src.strategies.signal import SignalType

from .types import OrderStatus, OrderType


@dataclass(slots=True)
class Order:
    """Represents a single order in the system.

    Designed to be generic so it can be reused for both backtesting and
    live trading. All state transitions happen via internal helpers to
    ensure invariants are preserved.
    """

    symbol: str
    side: SignalType  # BUY or SELL (HOLD is invalid for orders)
    order_type: OrderType
    quantity: int
    limit_price: Optional[float] = None
    stop_price: Optional[float] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    timeout: Optional[timedelta] = None  # auto-cancel after this duration

    # Internal / auto-filled fields ------------------------------------------------
    id: str = field(default_factory=lambda: uuid4().hex, init=False)
    filled_qty: int = 0
    status: OrderStatus = field(default=OrderStatus.PENDING, init=False)
    fills: List[FillEvent] = field(default_factory=list, init=False)

    # -------------------------------------------------------------------------
    def __post_init__(self) -> None:  # pragma: no cover
        if self.quantity <= 0:
            raise ValueError("quantity must be positive")
        if self.order_type == OrderType.LIMIT and self.limit_price is None:
            raise ValueError("limit_price required for LIMIT orders")
        if self.order_type == OrderType.STOP and self.stop_price is None:
            raise ValueError("stop_price required for STOP orders")
        if self.side == SignalType.HOLD:
            raise ValueError("Order side cannot be HOLD")

    # ---------------------------------------------------------------------
    @property
    def remaining(self) -> int:
        """Quantity yet to be filled."""

        return self.quantity - self.filled_qty

    # ---------------------------------------------------------------------
    def is_open(self) -> bool:
        """True if the order can still be executed/finalised."""

        return self.status in (OrderStatus.PENDING, OrderStatus.PARTIALLY_FILLED)

    # ---------------------------------------------------------------------
    def _record_fill(self, fill: FillEvent) -> None:
        """Update internal state with a new fill event."""

        self.fills.append(fill)
        self.filled_qty += fill.quantity
        if self.filled_qty >= self.quantity:
            self.status = OrderStatus.FILLED
        else:
            self.status = OrderStatus.PARTIALLY_FILLED

    # ---------------------------------------------------------------------
    def maybe_timeout(self, now: datetime) -> None:
        """Expire an order if its timeout has elapsed."""

        if self.timeout is None or not self.is_open():
            return
        if now - self.created_at > self.timeout:
            self.status = OrderStatus.EXPIRED

    # ---------------------------------------------------------------------
    def cancel(self) -> None:
        """Manually cancel the order if it is still open."""

        if self.is_open():
            self.status = OrderStatus.CANCELLED

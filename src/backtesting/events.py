from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from src.strategies.signal import SignalType


@dataclass(slots=True)
class MarketEvent:
    symbol: str
    time: datetime
    price: float
    row: dict[str, Any]


@dataclass(slots=True)
class SignalEvent:
    symbol: str
    time: datetime
    signal_type: SignalType
    confidence: float = 1.0


@dataclass(slots=True)
class OrderEvent:
    symbol: str
    time: datetime
    order_type: SignalType  # BUY / SELL only
    quantity: int
    price: float | None = None  # market if None


@dataclass(slots=True)
class FillEvent:
    symbol: str
    time: datetime
    fill_type: SignalType  # BUY / SELL
    quantity: int
    price: float
    commission: float = 0.0

from datetime import datetime, timedelta

import pytest

from src.orders.order import Order
from src.orders.order_book import OrderBook
from src.orders.types import OrderStatus, OrderType
from src.strategies.signal import SignalType


def test_market_order_full_fill() -> None:
    ob = OrderBook()
    order = Order(symbol="AAPL", side=SignalType.BUY, order_type=OrderType.MARKET, quantity=100)
    ob.add_order(order)
    now = datetime.utcnow()
    fills = ob.process_bar("AAPL", now, price=100.0, high=101.0, low=99.0)

    assert len(fills) == 1
    assert order.status == OrderStatus.FILLED
    assert order.filled_qty == 100


def test_limit_order_not_filled_when_price_not_reached() -> None:
    ob = OrderBook()
    order = Order(
        symbol="AAPL",
        side=SignalType.BUY,
        order_type=OrderType.LIMIT,
        quantity=100,
        limit_price=95.0,
    )
    ob.add_order(order)
    now = datetime.utcnow()
    fills = ob.process_bar("AAPL", now, price=100.0, high=100.0, low=96.0)

    assert not fills
    assert order.status == OrderStatus.PENDING


def test_order_timeout_expires() -> None:
    ob = OrderBook()
    created = datetime.utcnow()
    order = Order(
        symbol="AAPL",
        side=SignalType.BUY,
        order_type=OrderType.MARKET,
        quantity=100,
        timeout=timedelta(seconds=1),
    )
    # monkeypatch created_at for deterministic timeout evaluation
    order.created_at = created  # type: ignore[assignment]
    ob.add_order(order)

    later = created + timedelta(seconds=2)
    ob.process_bar("AAPL", later, price=100.0, high=101.0, low=99.0)

    assert order.status == OrderStatus.EXPIRED


def test_partial_fill_handling() -> None:
    ob = OrderBook(max_qty_per_fill=50)
    order = Order(symbol="AAPL", side=SignalType.SELL, order_type=OrderType.MARKET, quantity=120)
    ob.add_order(order)
    now = datetime.utcnow()
    # First bar should fill 50
    fills1 = ob.process_bar("AAPL", now, price=100.0, high=101.0, low=99.0)

    assert len(fills1) == 1
    assert order.status == OrderStatus.PARTIALLY_FILLED
    assert order.remaining == 70

    # Second bar should finish the order
    later = now + timedelta(minutes=1)
    fills2 = ob.process_bar("AAPL", later, price=99.0, high=100.5, low=98.0)

    assert order.status == OrderStatus.FILLED
    assert order.filled_qty == 120
    assert len(fills2) == 1

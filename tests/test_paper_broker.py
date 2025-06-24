from datetime import datetime, timedelta

import pytest

from src.broker.paper import PaperBroker
from src.orders.order import Order
from src.strategies.signal import SignalType
from src.orders.types import OrderType


@pytest.fixture
def broker():
    return PaperBroker(starting_cash=100_000, latency=timedelta(seconds=60), slippage_pct=0.001)


def test_latency_queues_order(broker):
    order = Order(symbol="AAPL", side=SignalType.BUY, order_type=OrderType.MARKET, quantity=10)  # MARKET
    now = datetime(2024, 1, 1, 9, 30)
    broker.submit_order(order, now)

    # Before latency expiry no orders active
    broker.on_price_tick("AAPL", now + timedelta(seconds=30), 100, 101, 99)
    assert order in broker.pending_orders()

    # After latency expiry order should be executed
    fills = broker.on_price_tick("AAPL", now + timedelta(seconds=61), 100, 101, 99)
    assert fills
    assert broker.portfolio.positions["AAPL"].quantity == 10


def test_slippage_applied(broker):
    order = Order(symbol="AAPL", side=SignalType.BUY, order_type=OrderType.MARKET, quantity=1)
    now = datetime.utcnow()
    broker.submit_order(order, now)

    fills = broker.on_price_tick("AAPL", now + broker.latency, 100, 100, 100)
    fill_price = fills[0].price
    assert fill_price == pytest.approx(100 * (1 + broker.slippage_pct))


def test_performance_report_generation(tmp_path, broker):
    # Simulate some ticks to build equity curve
    order = Order(symbol="AAPL", side=SignalType.BUY, order_type=OrderType.MARKET, quantity=10)
    start = datetime(2024, 1, 1, 9, 30)
    broker.submit_order(order, start)
    for i in range(10):
        t = start + broker.latency + timedelta(minutes=i)
        broker.on_price_tick("AAPL", t, 100 + i, 101 + i, 99 + i)

    report_path = broker.generate_performance_report(tmp_path / "paper.html")
    assert report_path.exists()


def test_reset_clears_state(broker):
    order = Order(symbol="AAPL", side=SignalType.BUY, order_type=OrderType.MARKET, quantity=1)
    broker.submit_order(order)
    broker.on_price_tick("AAPL", datetime.utcnow() + broker.latency, 100, 100, 100)

    assert broker.fills
    broker.reset()
    assert not broker.fills
    assert not broker.pending_orders()

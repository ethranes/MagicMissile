from datetime import datetime

import pytest

from src.backtesting.events import FillEvent
from src.portfolio.manager import PortfolioManager, Position
from src.strategies.signal import SignalType


@pytest.fixture
def pm():
    return PortfolioManager(starting_cash=100_000)


def _make_fill(symbol: str, side: SignalType, qty: int, price: float) -> FillEvent:
    return FillEvent(
        symbol=symbol,
        time=datetime.utcnow(),
        fill_type=side,
        quantity=qty,
        price=price,
        commission=1.0,
    )


def test_apply_fill_updates_cash_and_position(pm):
    fill = _make_fill("AAPL", SignalType.BUY, 10, 100.0)
    pm.apply_fill(fill)

    pos = pm.positions["AAPL"]
    assert pos.quantity == 10
    assert pos.avg_price == 100.0
    # 10*100 + 1 commission
    assert pm.cash == pytest.approx(100_000 - 1001.0)


def test_unrealised_pnl(pm):
    fill = _make_fill("AAPL", SignalType.BUY, 10, 50.0)
    pm.apply_fill(fill)

    prices = {"AAPL": 60.0}
    assert pm.unrealised_pnl(prices) == pytest.approx(10 * 10.0)


def test_size_for_risk(pm):
    size = pm.size_for_risk(price=50.0, cash_risk_pct=0.02)
    # risk dollars = 2000 -> 40 shares
    assert size == 40


def test_rebalance_to_target_weights(pm):
    # start with some positions
    pm.apply_fill(_make_fill("AAPL", SignalType.BUY, 50, 100.0))
    prices = {"AAPL": 100.0, "MSFT": 200.0}

    # target 50% each
    deltas = pm.rebalance_to_target_weights({"AAPL": 0.5, "MSFT": 0.5}, prices)

    # Should propose some buy of MSFT
    assert deltas["MSFT"] > 0


def test_persistence(tmp_path):
    pm = PortfolioManager(starting_cash=5000)
    pm.apply_fill(_make_fill("AAPL", SignalType.BUY, 5, 100.0))
    path = tmp_path / "state.json"
    pm.save(path)

    loaded = PortfolioManager.load(path)
    assert loaded.cash == pm.cash
    assert loaded.positions["AAPL"].quantity == 5


def test_margin_used_calculation(pm):
    """Cash can go negative up to leverage limit; margin_used reflects loan."""
    fill = _make_fill("AAPL", SignalType.BUY, 1200, 100.0)  # cost 120k + commission
    pm.apply_fill(fill)
    assert pm.cash < 0  # margin loan
    assert pm.margin_used == pytest.approx(-pm.cash)

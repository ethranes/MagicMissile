import importlib

import pandas as pd
import pytest

from src.strategies.registry import StrategyRegistry, registry
from src.strategies.signal import SignalType


def test_discovery_contains_buy_and_hold():
    assert "BuyAndHold" in registry.registry


def test_factory_and_generate():
    strat = registry.factory("BuyAndHold")
    idx = pd.date_range("2022-01-01", periods=2, freq="D")
    df = pd.DataFrame({"Close": [100, 101]}, index=idx)

    signals = strat.generate_signals(df)
    assert signals["AAPL"].type == SignalType.BUY


def test_duplicate_registration():
    reg = StrategyRegistry()
    # manual register once
    reg.register(registry.registry["BuyAndHold"])
    with pytest.raises(ValueError):
        reg.register(registry.registry["BuyAndHold"])  # duplicate

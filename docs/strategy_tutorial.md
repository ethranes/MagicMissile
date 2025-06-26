# Developing a Strategy

This tutorial walks you through building and testing a **Simple Moving-Average Crossover** strategy from scratch.

## 1. Scaffold the Class

Create `src/strategies/sma_crossover.py`:

```python
from datetime import timedelta
import pandas as pd
from pydantic import BaseModel, Field

from .base import BaseStrategy, Signal, SignalType

class SMAParams(BaseModel):
    fast: int = Field(20, gt=1, description="Fast window")
    slow: int = Field(50, gt=1, description="Slow window")

class SMACrossover(BaseStrategy):
    name = "SMA Crossover"
    params: SMAParams = SMAParams()

    def generate_signals(self, ohlcv: pd.DataFrame) -> dict[str, Signal]:
        close = ohlcv["Close"].ffill()
        fast = close.rolling(self.params.fast).mean()
        slow = close.rolling(self.params.slow).mean()
        cross_up = (fast > slow) & (fast.shift(1) <= slow.shift(1))

        if cross_up.iloc[-1]:
            return {
                self.symbol: Signal(
                    type=SignalType.BUY,
                    confidence=0.9,
                    time=ohlcv.index[-1] + timedelta(seconds=1),
                )
            }
        return {}
```

## 2. Register the Strategy

```python
from src.strategies.registry import StrategyRegistry
from src.strategies.sma_crossover import SMACrossover

StrategyRegistry.register(SMACrossover)
```

## 3. Backtest the Strategy

```bash
python run_backtest.py --symbol AAPL --strategy sma_crossover \
  --start 2021-01-01 --end 2023-01-01
```

The engine will output equity curve stats and drop a report in `reports/`.

## 4. Validate with Unit Tests

Create `tests/test_sma_crossover.py`:

```python
import pandas as pd
from src.strategies.sma_crossover import SMACrossover, SMAParams

def test_signal_generation():
    idx = pd.date_range("2024-01-01", periods=60)
    prices = pd.Series(range(60), index=idx)
    df = pd.DataFrame({"Close": prices})
    strat = SMACrossover(symbol="AAPL", params=SMAParams(fast=3, slow=5))
    signals = strat.generate_signals(df)
    assert isinstance(signals, dict)
```

Run `pytest -q` and ensure it passes.

## 5. Iterate & Deploy

Adjust parameters, add stop-loss logic, and deploy to live trading using `PaperBroker` first.

Happy trading!  
_Last updated: 2025-06-26._

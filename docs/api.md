# MagicMissile – API Reference

> Auto-generated overview of the public surface area. For detailed docstrings, see source files.

## Core Packages

| Package | Purpose |
|---------|---------|
| `src.core` | Application-wide settings, exceptions, logging. |
| `src.data` | Data providers, storage drivers, transformation utilities. |
| `src.strategies` | Base `Strategy` class, registry, built-in strategies. |
| `src.backtesting` | Backtest engine, metrics, reporting helpers. |
| `src.execution` | Broker abstractions, order routing, risk management. |
| `src.portfolio` | Real-time portfolio and position tracking. |
| `src.utils` | Helper utilities (validation, timing, etc.). |

## Key Classes

### Strategy Framework

```
class Strategy(Protocol):
    symbol: str | list[str]
    params: ParamModel

    def generate_signals(self, ohlcv: pd.DataFrame) -> dict[str, Signal]:
        ...
```

* Implement `generate_signals` to emit a `Signal` for each symbol.
* Validate parameters via a Pydantic `ParamModel`.

### Backtesting

* `BacktestEngine` – orchestrates event loop, feeds OHLCV to strategies, records fills.
* `metrics` – collection of stateless functions (Sharpe, drawdown, Calmar, etc.).

### Data Pipeline

* `DataPipeline` – async bulk / streaming ingestion with concurrency control.

### Execution & Orders

* `Order`, `OrderBook`, and `OrderManager` – life-cycle & audit trail.
* `PaperBroker` – simulated fills using real market data + slippage.

### Portfolio

* `PortfolioManager` – cash, margin, P&L, rebalancing logic.

## Exceptions hierarchy

```
DataProviderError
BacktestError
OrderValidationError
...
```

---

## Extending the Framework

1. **New Strategy** → subclass `BaseStrategy` and register it.
2. **New Broker** → implement `IBroker` interface in `src.execution.brokers`.
3. **New Data Provider** → subclass `DataProvider` and expose `.get_historical_data()`.

---

_Last updated: 2025-06-26._

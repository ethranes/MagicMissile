# MagicMissile Trading Bot

A modular, extensible Python framework for stock data ingestion, strategy development, backtesting, and live/paper trading.

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Fetch data and run example strategy
python main.py
```

## Strategies

The framework ships with sample strategies located in `src/strategies/`:

| Name | Description |
|------|-------------|
| BuyAndHold | Baseline buy-and-hold approach |
| SMACrossover | Fast/slow simple-moving-average crossover |
| RSIMeanReversion | RSI overbought / oversold mean-reversion |
| BollingerBands | Bollinger Bands breakout |

Each strategy defines a `ParamModel` (pydantic) for validation and can be registered dynamically through the `StrategyRegistry`.

## Backtesting & Reports

Use `BacktestEngine` to evaluate strategies over historical OHLCV DataFrames.

Test command for backtest engine: python run_backtest.py --symbol AAPL --strategy buy_and_hold --start 2020-01-01 --end 2021-01-01

```python
from pathlib import Path
from src.backtesting import BacktestEngine, summary, generate_html_report, generate_pdf_report
from src.strategies.buy_and_hold import BuyAndHoldStrategy

engine = BacktestEngine({"AAPL": df}, [BuyAndHoldStrategy()])
equity_curve = engine.run()
perf = summary(equity_curve)
html_path = generate_html_report(equity_curve, perf, Path("reports/buy_and_hold.html"))
pdf_path = generate_pdf_report(equity_curve, perf, Path("reports/buy_and_hold.pdf"))
print(f"HTML report: {html_path}\nPDF report: {pdf_path}")
```

Performance metrics (total return, Sharpe, drawdown, etc.) are available via `src.backtesting.metrics`.

## Paper Trading (Demo Account)

Run a live/paper session that polls quotes and executes trades in a simulated account:

```bash
python run_paper_trade.py --symbol AAPL --strategy buy_and_hold --refresh 60 --max-ticks 120
```

The script writes an interactive HTML report to `reports/` when it stops.

## Order Management

An in-memory `OrderBook` (`src/orders/order_book.py`) powers order matching during backtests.  The `Order` class encapsulates order details & lifecycle, while `OrderManager` provides additional validation and routing utilities.

Key features:

* Market, Limit, and Stop order support
* Status tracking (`PENDING → PARTIALLY_FILLED → FILLED / CANCELLED / EXPIRED`)
* Partial fill simulation via configurable liquidity cap
* Timeout and manual cancellation handling
* Complete audit trail through `OrderBook.history`.

## Project Structure
Refer to `PLANNING.md` for a full breakdown of directories and components.

## Documentation

Additional guides live under [`docs/`](docs/):

* [API Reference](docs/api.md)
* [Strategy Development Tutorial](docs/strategy_tutorial.md)
* [Configuration Guide](docs/configuration_guide.md)
* [Troubleshooting](docs/troubleshooting.md)
* [Performance Optimisation Tips](docs/performance_tips.md)
* [Deployment Guide](docs/deployment.md)

## Development

* Format code with `black .`
* Run tests with `pytest`
* Prefer `python -m venv .venv && source .venv/bin/activate` (or Windows equivalent) to keep dependencies isolated.

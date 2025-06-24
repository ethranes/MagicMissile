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

## Project Structure
Refer to `PLANNING.md` for a full breakdown of directories and components.

## Development

* Format code with `black .`
* Run tests with `pytest`
* Prefer `python -m venv .venv && source .venv/bin/activate` (or Windows equivalent) to keep dependencies isolated.

#!/usr/bin/env python3
"""Convenience CLI script to run a quick backtest and generate reports.

Example:
    python run_backtest.py --symbol AAPL --strategy buy_and_hold --start 2020-01-01 --end 2021-01-01
"""
from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path
from typing import Dict, Type

from loguru import logger

from src.data.providers.yahoo import YahooFinanceProvider
from src.backtesting import (
    BacktestEngine,
    summary,
    generate_html_report,
    generate_pdf_report,
)
from src.strategies.buy_and_hold import BuyAndHoldStrategy

# Mapping of strategy names to classes for simple demo purposes.
STRATEGY_REGISTRY: Dict[str, Type] = {
    "buy_and_hold": BuyAndHoldStrategy,
}

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a backtest and output reports.")
    parser.add_argument("--symbol", required=True, help="Ticker symbol to backtest, e.g. AAPL")
    parser.add_argument("--strategy", default="buy_and_hold", choices=STRATEGY_REGISTRY.keys())
    parser.add_argument("--start", required=True, help="Backtest start date YYYY-MM-DD")
    parser.add_argument("--end", required=True, help="Backtest end date YYYY-MM-DD")
    parser.add_argument("--outdir", default="reports", help="Directory to save reports")
    return parser.parse_args()

def main() -> None:
    args = parse_args()
    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    logger.info("Downloading data from Yahoo Finance: {}", args.symbol)
    data_provider = YahooFinanceProvider(cache=True)
    from datetime import datetime as _dt
    start_dt = _dt.fromisoformat(args.start)
    end_dt = _dt.fromisoformat(args.end)
    df = data_provider.get_historical_data(args.symbol, start_dt, end_dt)

    strategy_cls = STRATEGY_REGISTRY[args.strategy]
    strategy = strategy_cls()

    logger.info("Running backtest using {} strategy", args.strategy)
    engine = BacktestEngine({args.symbol: df}, [strategy])
    equity_df = engine.run()
    equity_curve = equity_df["equity"]
    perf = summary(equity_df["equity"])

    html_path = generate_html_report(
        equity_df["equity"],
        perf,
        outdir / f"{args.strategy}_{args.symbol}.html",
    )
    logger.success("HTML report saved: {}", html_path)

    # Try PDF export if kaleido is available.
    try:
        pdf_path = generate_pdf_report(
            equity_df["equity"],
            perf,
            outdir / f"{args.strategy}_{args.symbol}.pdf",
        )
        logger.success("PDF report saved: {}", pdf_path)
    except (ModuleNotFoundError, ValueError) as e:
        logger.warning("PDF export skipped: {}", e)

if __name__ == "__main__":
    main()

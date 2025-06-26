#!/usr/bin/env python3
"""Run a live *paper* trading session against a demo account (PaperBroker).

The loop periodically fetches the latest price via a `DataProvider`, feeds the
bar into `PaperBroker`, queries the selected strategy for new signals and
submits any resulting orders.  When the session ends (max-ticks reached or
Ctrl-C), an interactive HTML performance report is written to the reports
folder, similar to the back-testing report.

Example
-------
python run_paper_trade.py \
    --symbol AAPL \
    --strategy buy_and_hold \
    --history-start 2024-01-01 \
    --refresh 60 \
    --max-ticks 120
"""
from __future__ import annotations

import argparse
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Type

from loguru import logger

from src.data.providers.yahoo import YahooFinanceProvider  # default provider
from src.broker.paper import PaperBroker
from src.orders.order import Order
from src.orders.types import OrderType
from src.strategies.signal import SignalType
from src.backtesting.report import generate_html_report
from src.backtesting.metrics import summary
from src.core.exceptions import DataProviderError

# ---------------------------------------------------------------------------
# Strategy registry ----------------------------------------------------------
# We use the same lightweight approach as run_backtest.py to avoid a hard
# dependency on a plugin registry.  Extend this mapping as you add more
# built-in strategies.
# ---------------------------------------------------------------------------
from src.strategies.buy_and_hold import BuyAndHoldStrategy

STRATEGY_REGISTRY: Dict[str, Type] = {
    "buy_and_hold": BuyAndHoldStrategy,
    # "sma_crossover": SMACrossover,  # Example: uncomment when added
}

# ---------------------------------------------------------------------------
# Helpers --------------------------------------------------------------------
# ---------------------------------------------------------------------------

def _signal_to_order(symbol: str, sig_type: SignalType, quantity: int = 1) -> Order:
    """Convert a simple BUY/SELL *SignalType* into a market *Order*.

    Args:
        symbol: Ticker the signal relates to.
        sig_type: BUY or SELL.
        quantity: Number of shares. Positive integer.
    """

    return Order(
        symbol=symbol,
        side=sig_type,
        order_type=OrderType.MARKET,
        quantity=quantity,
    )

# ---------------------------------------------------------------------------
# CLI ------------------------------------------------------------------------
# ---------------------------------------------------------------------------

def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Run a paper-trading session.")
    p.add_argument("--symbol", required=True, help="Ticker symbol, e.g. AAPL")
    p.add_argument(
        "--strategy",
        default="buy_and_hold",
        choices=STRATEGY_REGISTRY.keys(),
        help="Strategy identifier",
    )
    p.add_argument(
        "--history-start",
        default="2024-01-01",
        help="ISO date for historical warm-up (YYYY-MM-DD)",
    )
    p.add_argument(
        "--refresh",
        type=int,
        default=60,
        help="Seconds between price polls",
    )
    p.add_argument(
        "--max-ticks",
        type=int,
        default=0,
        help="Stop after this many price updates (0 = run until Ctrl-C)",
    )
    p.add_argument(
        "--cash",
        type=float,
        default=100_000,
        help="Starting cash for the demo account",
    )
    p.add_argument(
        "--slippage",
        type=float,
        default=0.0005,
        help="Fractional slippage applied to executed trades",
    )
    p.add_argument(
        "--latency",
        type=float,
        default=2.0,
        help="Artificial latency (seconds) before orders reach the book",
    )
    p.add_argument(
        "--outdir",
        default="reports",
        help="Directory to store HTML report",
    )
    return p.parse_args(argv)

# ---------------------------------------------------------------------------
# Main loop ------------------------------------------------------------------
# ---------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> None:  # pragma: no cover
    args = _parse_args(argv)
    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    # ---------------------------------------------------------------------
    # Initialise components -----------------------------------------------
    # ---------------------------------------------------------------------
    provider = YahooFinanceProvider(cache=True)

    history_start = datetime.fromisoformat(args.history_start)
    logger.info("Downloading historical data from {} to warm-up indicators", history_start.date())
    try:
        hist_df = provider.get_historical_data(args.symbol, history_start, datetime.utcnow())
    except DataProviderError as e:
        logger.warning("Historical data fetch failed: {} – continuing with empty warm-up.", e)
        import pandas as pd
        hist_df = pd.DataFrame(columns=["Close"])

    strategy_cls = STRATEGY_REGISTRY[args.strategy]
    strategy = strategy_cls()  # Strategies currently take no params via CLI

    broker = PaperBroker(
        starting_cash=args.cash,
        latency=timedelta(seconds=args.latency),
        slippage_pct=args.slippage,
    )

    logger.success(
        "Paper-trading started  |  symbol={}  strategy={}  cash=${:,.0f}",
        args.symbol,
        args.strategy,
        args.cash,
    )

    # ------------------------------------------------------------------
    # Live loop ---------------------------------------------------------
    # ------------------------------------------------------------------
    tick = 0
    try:
        while True:
            tick += 1
            now = datetime.utcnow()
            try:
                quote = provider.get_real_time_quote(args.symbol)
            except DataProviderError as e:
                logger.error("Quote fetch failed: {} – retrying after {}s", e, args.refresh)
                time.sleep(max(args.refresh, 1))
                continue
            price = float(quote["price"])

            # Feed tick to broker (OHLC simplification)
            broker.on_price_tick(args.symbol, now, price, price, price)

            # Append to history & query strategy
            hist_df.loc[now] = price
            signals = strategy.generate_signals(hist_df)
            sig = signals.get(args.symbol)
            if sig and sig.type in (SignalType.BUY, SignalType.SELL):
                order = _signal_to_order(args.symbol, sig.type)
                broker.submit_order(order, now)
                logger.info("Submitted {} order at {:.2f}", sig.type, price)

            equity = broker.equity({args.symbol: price})
            logger.info("Tick {} | {} ${:.2f}", tick, now.strftime("%H:%M:%S"), equity)

            # Termination conditions
            if args.max_ticks and tick >= args.max_ticks:
                logger.info("Max ticks reached – stopping session")
                break
            time.sleep(max(args.refresh, 1))
    except KeyboardInterrupt:
        logger.warning("Session interrupted by user – generating report…")

    # ------------------------------------------------------------------
    # Report generation -------------------------------------------------
    # ------------------------------------------------------------------
    equity_curve = broker._equity_curve  # list[(ts, equity)]
    if not equity_curve:
        logger.error("No equity data captured – nothing to report")
        sys.exit(1)
    times, equities = zip(*equity_curve)
    import pandas as pd

    ser = pd.Series(equities, index=pd.to_datetime(times), name="equity")
    report_path = generate_html_report(ser, summary(ser), outdir / f"paper_{args.symbol}.html", trades=broker.fills)
    logger.success("HTML performance report written to {}", report_path)


if __name__ == "__main__":  # pragma: no cover
    main()

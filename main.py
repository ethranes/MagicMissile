from datetime import datetime, timedelta

import pandas as pd
from loguru import logger

from src.core.config import Config
from src.core.logging_config import setup_logging
from src.data.providers.yahoo import YahooFinanceProvider
from src.strategies.buy_and_hold import BuyAndHoldStrategy


def run() -> None:
    # Setup logging
    setup_logging(level="INFO")

    # Load configuration
    cfg = Config.load("config/config.yaml")
    logger.info(f"Loaded configuration: {cfg}")

    # Fetch data
    provider = YahooFinanceProvider()
    end_date = datetime.today()
    start_date = end_date - timedelta(days=365)
    logger.info("Fetching historical data for AAPL...")
    data: pd.DataFrame = provider.get_historical_data("AAPL", start_date, end_date)
    logger.info(f"Retrieved {len(data)} rows of data")

    # Run strategy
    strategy = BuyAndHoldStrategy()
    signal = strategy.generate_signals(data)
    logger.info(f"Generated signal: {signal}")


if __name__ == "__main__":
    run()

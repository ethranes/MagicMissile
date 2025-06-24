class TradingBotError(Exception):
    """Base exception for trading bot errors."""


class ConfigError(TradingBotError):
    """Raised when configuration validation fails."""


class DataProviderError(TradingBotError):
    """Raised for errors occurring in data provider operations."""


class StrategyError(TradingBotError):
    """Raised when a strategy encounters an error."""


class ExecutionError(TradingBotError):
    """Raised for order execution failures."""

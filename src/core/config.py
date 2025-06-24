from pathlib import Path
from typing import Any, Dict

import yaml
from pydantic import BaseModel, Field, ValidationError
from pydantic_settings import BaseSettings, SettingsConfigDict


class AppSettings(BaseModel):
    """Application-wide settings loaded from YAML.

    Attributes:
        env (str): Environment name (e.g., dev, prod).
        data_dir (str): Local directory for downloaded data.
        log_level (str): Log level for the application.
    """

    env: str = Field(default="dev")
    data_dir: str = Field(default="data")
    log_level: str = Field(default="INFO")




class DataProviderSettings(BaseModel):
    """Settings related to the chosen data source."""

    name: str = Field(default="yahoo", description="Identifier for the data provider implementation")
    cache: bool = Field(default=False, description="Enable local caching of downloaded data")


class BrokerSettings(BaseModel):
    """Broker API credentials and options."""

    name: str = Field(default="paper", description="Broker identifier or mode (paper/live)")
    api_key: str | None = Field(default=None)
    api_secret: str | None = Field(default=None)


class StrategySettings(BaseModel):
    """Top-level strategy configuration and runnable parameters."""

    name: str = Field(default="BuyAndHold")
    parameters: Dict[str, Any] = Field(default_factory=dict)





class Config(BaseSettings):
    """Root configuration object.

    This class loads a YAML file and validates it using pydantic. Environment
    variables override YAML values automatically via `BaseSettings`.

    Args:
        path (str | Path): Path to a YAML config file.
    """

    app: AppSettings
    data_provider: DataProviderSettings = Field(default_factory=DataProviderSettings)
    broker: BrokerSettings = Field(default_factory=BrokerSettings)
    strategy: StrategySettings = Field(default_factory=StrategySettings)

    model_config = SettingsConfigDict(
        extra="forbid",
        env_nested_delimiter="__",
        case_sensitive=False,
    )

    @classmethod
    def load(cls, path: str | Path) -> "Config":
        """Load configuration from YAML and environment variables.

        Args:
            path: YAML file path.

        Returns:
            Config: Validated configuration instance.
        """

        path = Path(path)
        if not path.is_file():
            raise FileNotFoundError(f"Config file not found: {path}")

        with path.open("r", encoding="utf-8") as f:
            raw: Dict[str, Any] = yaml.safe_load(f) or {}

        # Apply environment variable overrides manually so they take precedence
        import os

        for env_key, env_val in os.environ.items():
            if "__" not in env_key:
                continue
            parts = env_key.lower().split("__")  # e.g., APP__ENV -> ["app", "env"]
            current: Dict[str, Any] = raw
            for part in parts[:-1]:
                current = current.setdefault(part, {})  # type: ignore[assignment]
            current[parts[-1]] = env_val

        try:
            return cls(**raw)  # type: ignore[arg-type]
        except ValidationError as err:
            raise ValueError(f"Invalid configuration:\n{err}") from err

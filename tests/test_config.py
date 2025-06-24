from pathlib import Path

from src.core.config import Config


def test_config_loading(tmp_path: Path) -> None:
    cfg_file = tmp_path / "config.yaml"
    cfg_file.write_text(
        """
app:
  env: test
  data_dir: /tmp/data
  log_level: DEBUG

data_provider:
  name: yahoo
  cache: true

broker:
  name: paper
  api_key: KEY
  api_secret: SECRET

strategy:
  name: BuyAndHold
  parameters:
    threshold: 0.1
"""
    )

    cfg = Config.load(cfg_file)

    # App settings
    assert cfg.app.env == "test"
    assert cfg.app.data_dir == "/tmp/data"
    assert cfg.app.log_level == "DEBUG"

    # Data provider
    assert cfg.data_provider.name == "yahoo"
    assert cfg.data_provider.cache is True

    # Broker
    assert cfg.broker.api_key == "KEY"
    assert cfg.broker.api_secret == "SECRET"

    # Strategy
    assert cfg.strategy.name == "BuyAndHold"
    assert cfg.strategy.parameters["threshold"] == 0.1

    # Environment variable override (nested)
    import os

    os.environ["APP__ENV"] = "prod"
    cfg_env = Config.load(cfg_file)
    assert cfg_env.app.env == "prod"
    del os.environ["APP__ENV"]

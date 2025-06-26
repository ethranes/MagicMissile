# Configuration Guide

All user-facing configuration lives in **YAML** files under `config/`.

| File | Purpose |
|------|---------|
| `settings.yaml` | Global app settings (DB path, logging level, cache TTL). |
| `strategies.yaml` | List of active strategies and their parameter overrides. |
| `brokers.yaml` | Live / paper broker credentials and options. |

## 1. settings.yaml

```yaml
# config/settings.yaml
logging:
  level: INFO
  file: logs/app.log

database:
  url: sqlite:///data/missile.db
cache:
  redis_url: redis://localhost:6379/0
```

## 2. strategies.yaml

```yaml
# config/strategies.yaml
- name: BuyAndHoldStrategy
  symbol: AAPL
  params: {}
- name: SMACrossover
  symbol: MSFT
  params:
    fast: 20
    slow: 50
```

## 3. brokers.yaml

```yaml
alpaca:
  key_id: YOUR_KEY
  secret: YOUR_SECRET
  paper: true
```

Load config in code:

```python
from src.core.config import Settings
settings = Settings.from_yaml("config/settings.yaml")
```

Tip: environment variables override YAML via `pydantic-settings`.

_Last updated: 2025-06-26._

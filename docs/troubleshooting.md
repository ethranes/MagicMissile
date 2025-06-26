# Troubleshooting

| Symptom | Possible Cause | Fix |
|---------|----------------|-----|
| `DataProviderError: 429` | API rate-limit exceeded | Reduce call frequency, add API key, or set `provider.throttle=True`. |
| Backtest seems stuck / slow | Large symbol universe or high-freq data | Use smaller date range; enable `--progress` CLI flag to monitor. |
| `OrderValidationError` | Invalid quantity / price | Ensure order qty > 0 and price > 0. |
| `fill_method` deprecation warning | pandas 2.2 change | Upgrade `MagicMissile>=0.2.1` where fix is applied. |
| SQLite DB locked | Simultaneous writers | Use Postgres or run only one pipeline instance. |

## Debugging Tips

* Run with `LOG_LEVEL=DEBUG` to see SQL and event queue logs.
* Use `pytest -s -k <test>` to reproduce failing cases interactively.
* Add `@log_timing()` decorator (see `src.core.logging_config`) to time slow functions.

_Last updated: 2025-06-26._

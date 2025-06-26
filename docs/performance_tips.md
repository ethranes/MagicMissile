# Performance Optimisation Tips

1. **Vectorise whenever possible** – avoid Python loops over tick data; rely on NumPy/Pandas.
2. **Leverage async** – `DataPipeline.stream()` supports concurrent fetches via `asyncio.Semaphore`.
3. **Enable C extensions** – install `numpy`, `pandas`, and optionally `pyarrow` for faster I/O.
4. **Cache** – Redis caching layer cuts repeated provider calls (`src.data.providers.base.BaseProvider.cache`).
5. **Profile** – run `python -m cProfile -m run_backtest ...` and inspect with `snakeviz`.
6. **Batch DB writes** – `upsert_historical_df` already groups inserts in one transaction.
7. **Use rolling windows smartly** – for long series, prefer `numba`-accelerated routines or downsample.

_Last updated: 2025-06-26._

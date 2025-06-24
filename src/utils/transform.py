from __future__ import annotations

import pandas as pd

_OHLCV_ORDER = ["Open", "High", "Low", "Close", "Volume"]


def normalize_ohlcv(df: pd.DataFrame) -> pd.DataFrame:
    """Return *df* with canonical OHLCV column order and capitalized names."""

    df = df.copy()
    df.columns = [c.capitalize() for c in df.columns]
    missing = [c for c in _OHLCV_ORDER if c not in df.columns]
    if missing:
        raise ValueError(f"Missing OHLCV columns: {', '.join(missing)}")
    return df[_OHLCV_ORDER]

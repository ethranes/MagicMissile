from __future__ import annotations

from datetime import date
from typing import List

import pandas as pd
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from .models import MarketData


# ------------------ insertion utilities ------------------

def upsert_historical_df(symbol: str, df: pd.DataFrame, session: Session) -> None:
    """Insert or update historical data from *df* for *symbol*.

    The DataFrame must have its index named "date" and contain Open/High/Low/Close/Volume columns.
    """

    if df.empty:
        return

    df = df.copy()
    # Ensure the index holds python datetime (normalize) for flexibility
    df.index = pd.to_datetime(df.index).normalize()
    df.index.name = "date"
    df["symbol"] = symbol.upper()
    records = df.reset_index().to_dict(orient="records")

    for rec in records:
        obj = MarketData(
            symbol=rec["symbol"],
            date=pd.to_datetime(rec["date"]).date(),
            open=float(rec["Open"]),
            high=float(rec["High"]),
            low=float(rec["Low"]),
            close=float(rec["Close"]),
            volume=int(rec["Volume"]),
        )
        session.merge(obj)
    session.flush()


# ------------------ retrieval utilities ------------------

def load_historical_df(symbol: str, start: date, end: date, session: Session) -> pd.DataFrame:
    stmt = (
        select(MarketData)
        .where(
            MarketData.symbol == symbol.upper(),
            MarketData.date >= start,
            MarketData.date <= end,
        )
        .order_by(MarketData.date)
    )
    rows: List[MarketData] = session.scalars(stmt).all()  # type: ignore[arg-type]
    if not rows:
        return pd.DataFrame()
    data = {
        "date": [r.date for r in rows],
        "Open": [r.open for r in rows],
        "High": [r.high for r in rows],
        "Low": [r.low for r in rows],
        "Close": [r.close for r in rows],
        "Volume": [r.volume for r in rows],
    }
    df = pd.DataFrame(data).set_index("date")
    return df


# ------------------ cleanup utilities ------------------

def cleanup_before(symbol: str, before: date, session: Session) -> int:
    stmt = delete(MarketData).where(
        MarketData.symbol == symbol.upper(),
        MarketData.date < before,
    )
    res = session.execute(stmt)
    return res.rowcount  # type: ignore[return-value]

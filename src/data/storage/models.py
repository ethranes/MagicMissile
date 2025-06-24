from __future__ import annotations

from datetime import date

from sqlalchemy import BigInteger, Column, Date, Float, Integer, String, UniqueConstraint
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class MarketData(Base):
    """OHLCV market data for a symbol and date."""

    __tablename__ = "market_data"
    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String(10), nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)
    open = Column(Float, nullable=False)
    high = Column(Float, nullable=False)
    low = Column(Float, nullable=False)
    close = Column(Float, nullable=False)
    volume = Column(BigInteger, nullable=False)

    __table_args__ = (
        UniqueConstraint("symbol", "date", name="uq_symbol_date"),
    )

    # Helpful representation
    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"<MarketData {self.symbol} {self.date} O:{self.open} H:{self.high} L:{self.low}"
            f" C:{self.close} V:{self.volume}>"
        )

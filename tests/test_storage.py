from datetime import date

import pandas as pd
import pytest

from src.data.storage.database import get_engine, get_session, init_engine
from src.data.storage.migrations import run_migrations
from src.data.storage.repository import cleanup_before, load_historical_df, upsert_historical_df


@pytest.fixture(scope="module")
def engine():
    eng = get_engine("sqlite:///:memory:")
    run_migrations(eng)
    return eng


from sqlalchemy.orm import sessionmaker


@pytest.fixture()
def session(engine):
    SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
    sess = SessionLocal()
    try:
        yield sess
        sess.commit()
    finally:
        sess.close()


@pytest.fixture()
def sample_df():
    idx = [d.date() for d in pd.date_range("2022-01-01", periods=3, freq="D")]
    df = pd.DataFrame({
        "Open": [1.0, 1.1, 1.2],
        "High": [1.0, 1.1, 1.2],
        "Low": [1.0, 1.1, 1.2],
        "Close": [1.0, 1.1, 1.2],
        "Volume": [100, 101, 102],
    }, index=idx)
    df.index.name = "date"
    df.index.name = "date"
    return df


def test_insert_and_retrieve(session, sample_df):
    upsert_historical_df("AAPL", sample_df, session)

    fetched = load_historical_df("AAPL", date(2022, 1, 1), date(2022, 1, 3), session)
    assert not fetched.empty
    pd.testing.assert_frame_equal(fetched, sample_df)


def test_cleanup(session):
    removed = cleanup_before("AAPL", date(2022, 1, 2), session)
    assert removed == 1

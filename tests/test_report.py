from pathlib import Path
import importlib.util, pytest

if importlib.util.find_spec("plotly") is None:  # pragma: no cover
    pytest.skip("plotly not installed", allow_module_level=True)

import pandas as pd

from src.backtesting.metrics import PerformanceSummary
from src.backtesting.report import generate_html_report, generate_pdf_report, save_comparison_chart_html


def test_generate_html_report(tmp_path: Path):
    idx = pd.date_range("2023-01-01", periods=5, freq="D")
    equity = pd.Series([100, 101, 103, 102, 105], index=idx)
    summary = PerformanceSummary(
        total_return=0.05,
        annualized_return=0.3,
        sharpe_ratio=1.2,
        sortino_ratio=1.4,
        max_drawdown=-0.02,
        max_drawdown_duration=1,
        volatility=0.15,
        calmar_ratio=15.0,
    )

    out = generate_html_report(equity, summary, tmp_path / "report.html")
    assert out.exists()
    content = out.read_text()
    assert "Equity Curve" in content
    assert "Performance Summary" in content


def test_generate_pdf_and_comparison(tmp_path: Path):
    import importlib.util, pytest
    if importlib.util.find_spec("kaleido") is None:
        pytest.skip("kaleido not installed")
    idx = pd.date_range("2023-01-01", periods=5, freq="D")
    equity1 = pd.Series([100, 101, 103, 102, 105], index=idx)
    equity2 = pd.Series([100, 100, 102, 103, 104], index=idx)
    summary = PerformanceSummary(
        total_return=0.05,
        annualized_return=0.3,
        sharpe_ratio=1.2,
        sortino_ratio=1.4,
        max_drawdown=-0.02,
        max_drawdown_duration=1,
        volatility=0.15,
        calmar_ratio=15.0,
    )

    pdf_out = generate_pdf_report(equity1, summary, tmp_path / "report.pdf")
    assert pdf_out.exists() and pdf_out.stat().st_size > 0

    comp_out = save_comparison_chart_html({"StratA": equity1, "StratB": equity2}, tmp_path / "compare.html")
    assert comp_out.exists()

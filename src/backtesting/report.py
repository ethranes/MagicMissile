"""Backtesting report generation utilities.

Generates interactive HTML reports including:
1. Equity curve plot
2. Drawdown plot
3. Trade distribution histogram (if trades provided)
4. Performance metrics table

Designed to integrate with BacktestEngine results.
"""
from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd

try:
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots
except ModuleNotFoundError:  # pragma: no cover
    go = None  # type: ignore
    make_subplots = None  # type: ignore

from src.backtesting.events import FillEvent
from src.backtesting.metrics import PerformanceSummary, rolling_sharpe_ratio

# ---------------------------------------------------------------------------


def _drawdown_series(equity: pd.Series) -> pd.Series:
    """Percentage drawdown series."""
    return equity / equity.cummax() - 1.0


class ReportGenerator:
    """Create interactive HTML backtest reports using Plotly."""

    def __init__(
        self,
        equity: pd.Series,
        summary: PerformanceSummary,
        trades: Optional[List[FillEvent]] = None,
        benchmark: Optional[pd.Series] = None,
    ) -> None:
        self.equity = equity
        self.summary = summary
        self.trades = trades or []
        self.benchmark = benchmark

    # ---------------------------------------------------------------------

    def build_figure(self) -> go.Figure:
        """Return a Plotly figure with equity/drawdown (and optionally benchmark)."""
        rows = 3 if self.trades else 2
        subplot_titles = ["Equity Curve", "Drawdown (%)"]
        if self.trades:
            subplot_titles.append("Trade P&L Distribution")

        fig = make_subplots(rows=rows, cols=1, shared_xaxes=True, vertical_spacing=0.06, subplot_titles=subplot_titles)

        # Equity curve
        fig.add_trace(go.Scatter(x=self.equity.index, y=self.equity, name="Equity"), row=1, col=1)
        if self.benchmark is not None:
            fig.add_trace(go.Scatter(x=self.benchmark.index, y=self.benchmark, name="Benchmark"), row=1, col=1)

        # Drawdown
        dd = _drawdown_series(self.equity) * 100.0  # percentage
        fig.add_trace(go.Scatter(x=dd.index, y=dd, name="Drawdown", line=dict(color="firebrick")), row=2, col=1)

        # Trade distribution
        if self.trades:
            pnls = []
            open_pos: Dict[str, FillEvent] = {}
            for f in self.trades:
                if f.fill_type.name == "BUY":
                    open_pos[f.symbol] = f
                elif f.fill_type.name == "SELL" and f.symbol in open_pos:
                    entry = open_pos.pop(f.symbol)
                    pnls.append((f.price - entry.price) * entry.quantity)
            if pnls:
                fig.add_trace(go.Histogram(x=pnls, name="Trade P&L", marker_color="royalblue"), row=3, col=1)

        fig.update_layout(height=600 + (rows - 2) * 200, title="Backtest Report", showlegend=True)
        fig.update_yaxes(ticksuffix="%", row=2, col=1)
        return fig

    # ------------------------------------------------------------------

    def to_html(self, output_path: str | Path) -> Path:
        """Save report as standalone HTML and return the path."""
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        fig = self.build_figure()

        # Append metrics summary as HTML table under the graph
        metrics_table = pd.DataFrame([asdict(self.summary)]).T
        metrics_table.columns = ["Value"]
        table_html = metrics_table.to_html(float_format=lambda x: f"{x:.4f}" if isinstance(x, float) else x)

        html = fig.to_html(full_html=False, include_plotlyjs="cdn")
        full_html = f"""
        <html><head><meta charset='utf-8'><title>Backtest Report</title></head>
        <body>
        {html}
        <h2>Performance Summary</h2>
        {table_html}
        </body></html>
        """
        output_path.write_text(full_html)
        return output_path

    # ------------------------------------------------------------------

    def to_pdf(self, output_path: str | Path) -> Path:
        """Save report as PDF (static image of charts). Requires 'kaleido'."""
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        fig = self.build_figure()
        fig.write_image(str(output_path), format="pdf")
        return output_path


# Convenience ----------------------------------------------------------------

def generate_html_report(
    equity: pd.Series,
    summary: PerformanceSummary,
    output_path: str | Path,
    trades: Optional[List[FillEvent]] = None,
    benchmark: Optional[pd.Series] = None,
) -> Path:
    """One-liner helper to write a report and get the path back."""
    generator = ReportGenerator(equity, summary, trades, benchmark)
    return generator.to_html(output_path)


def generate_pdf_report(
    equity: pd.Series,
    summary: PerformanceSummary,
    output_path: str | Path,
    trades: Optional[List[FillEvent]] = None,
    benchmark: Optional[pd.Series] = None,
) -> Path:
    """Generate and save a PDF report using Kaleido backend."""
    generator = ReportGenerator(equity, summary, trades, benchmark)
    return generator.to_pdf(output_path)


# ---------------------------------------------------------------------------
# Strategy comparison --------------------------------------------------------


def comparison_equity_chart(equity_curves: Dict[str, pd.Series]) -> go.Figure:  # noqa: D401
    """Return a Plotly figure comparing multiple strategy equity curves."""
    fig = go.Figure()
    for name, series in equity_curves.items():
        fig.add_trace(go.Scatter(x=series.index, y=series, name=name))
    fig.update_layout(
        title="Strategy Equity Curve Comparison",
        yaxis_title="Equity",
        xaxis_title="Date",
        template="plotly_white",
    )
    return fig


def save_comparison_chart_html(equity_curves: Dict[str, pd.Series], output_path: str | Path) -> Path:
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig = comparison_equity_chart(equity_curves)
    fig.write_html(str(output_path), include_plotlyjs="cdn")
    return output_path


def save_comparison_chart_pdf(equity_curves: Dict[str, pd.Series], output_path: str | Path) -> Path:
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig = comparison_equity_chart(equity_curves)
    fig.write_image(str(output_path), format="pdf")
    return output_path

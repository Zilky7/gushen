from __future__ import annotations

from dataclasses import asdict

from app.services.backtest import (
    SAMPLE_OUT_OF_SAMPLE,
    SAMPLE_RESEARCH,
    assert_isolated_research_window,
    run_daily_backtest,
)
from app.services.market_data import MarketDataService


class ResearchService:
    """Runs baseline reports with a hard research/OOS wall; no LLM is called here."""

    def __init__(self, market_data: MarketDataService) -> None:
        self.market_data = market_data

    def baseline_report(self, symbol: str) -> dict:
        assert_isolated_research_window(SAMPLE_RESEARCH.start, SAMPLE_RESEARCH.end)
        research_bars = self.market_data.get_history_bars(
            symbol, SAMPLE_RESEARCH.start, SAMPLE_RESEARCH.end
        )
        oos_bars = self.market_data.get_history_bars(
            symbol, SAMPLE_OUT_OF_SAMPLE.start, SAMPLE_OUT_OF_SAMPLE.end
        )
        return {
            "symbol": symbol.upper(),
            "strategy_version": "baseline-2026-07-20",
            "research_window": asdict(SAMPLE_RESEARCH),
            "out_of_sample_window": asdict(SAMPLE_OUT_OF_SAMPLE),
            "baseline_research": asdict(run_daily_backtest(research_bars)),
            "baseline_out_of_sample": asdict(run_daily_backtest(oos_bars)),
            "note": "No parameter proposal is automatically adopted; 2026 H1 remains isolated from optimization.",
        }

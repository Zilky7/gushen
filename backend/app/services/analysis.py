from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from app.domain.models import AnalysisResult, IndicatorPoint
from app.engine.defaults import DEFAULT_PARAMETERS, STRATEGY_VERSION
from app.repositories import AnalysisRepository
from app.services.market_data import MarketDataService


class AnalysisService:
    def __init__(self, market_data: MarketDataService, analyses: AnalysisRepository) -> None:
        self.market_data = market_data
        self.analyses = analyses

    def analyze(self, symbol: str) -> AnalysisResult:
        import pandas as pd

        market = self.market_data.get_daily_bars(symbol)
        frame = pd.DataFrame(
            [bar.model_dump() for bar in market.bars]
        ).set_index("date").rename(columns={"open": "Open", "high": "High", "low": "Low", "close": "Close", "volume": "Volume"})
        candidates = []
        zones = []
        indicators: list[IndicatorPoint] = []
        if len(frame) >= DEFAULT_PARAMETERS.sma_slow:
            from app.engine.indicators import compute_indicators
            from app.engine.strategy import generate_candidates
            from app.engine.zones import build_price_zones, find_pivots

            enriched = compute_indicators(frame)
            indicators = [
                IndicatorPoint(
                    date=index,
                    sma_20=None if pd.isna(row.sma_20) else float(row.sma_20),
                    sma_50=None if pd.isna(row.sma_50) else float(row.sma_50),
                    sma_200=None if pd.isna(row.sma_200) else float(row.sma_200),
                )
                for index, row in enriched.iterrows()
            ]
            latest = enriched.iloc[-1]
            pivot_bars = [
                {"date": item.date, "high": item.high, "low": item.low}
                for item in market.bars
            ]
            pivots = find_pivots(pivot_bars, DEFAULT_PARAMETERS.pivot_width)
            if pd.notna(latest["atr_14"]):
                zones = build_price_zones(
                    pivots, float(latest["atr_14"]), float(latest["Close"]), market.bars[-1].date
                )
            candidates = generate_candidates(frame, zones)
        result = AnalysisResult(
            id=str(uuid4()),
            symbol=market.symbol,
            created_at=datetime.now(UTC),
            data_updated_at=market.updated_at,
            stale_cache=market.stale_cache,
            data_source=market.source,
            strategy_version=STRATEGY_VERSION,
            bars=market.bars,
            indicators=indicators,
            zones=zones,
            candidates=candidates,
        )
        self.analyses.save_analysis(result)
        return result

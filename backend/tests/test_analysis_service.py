from datetime import date, datetime, timezone

from app.db import Database
from app.domain.models import Direction, OhlcvBar, OpportunityStatus, PriceRange, StrategyCandidate
from app.repositories import AnalysisRepository
from app.services.analysis import AnalysisService, apply_explanation
from app.services.llm import Explanation
from app.services.market_data import MarketDataResult


def test_analysis_requires_enough_daily_data(tmp_path) -> None:
    class Data:
        def get_daily_bars(self, symbol: str) -> MarketDataResult:
            return MarketDataResult(
                symbol="MU",
                bars=[OhlcvBar(date=date(2026, 1, 1), open=1, high=2, low=1, close=2, volume=3)],
                updated_at=datetime.now(timezone.utc),
                stale_cache=False,
            )

    service = AnalysisService(Data(), AnalysisRepository(Database(tmp_path / "analysis.sqlite3")))

    result = service.analyze("MU")

    assert result.symbol == "MU"
    assert result.candidates == []


def test_analysis_exposes_indicator_series_for_charting(tmp_path) -> None:
    bars = [
        OhlcvBar(date=date(2025, 1, 1).fromordinal(date(2025, 1, 1).toordinal() + index), open=100 + index, high=101 + index, low=99 + index, close=100 + index, volume=1000)
        for index in range(210)
    ]
    class Data:
        def get_daily_bars(self, symbol: str) -> MarketDataResult:
            return MarketDataResult("MU", bars, datetime.now(timezone.utc), False)

    result = AnalysisService(Data(), AnalysisRepository(Database(tmp_path / "analysis.sqlite3"))).analyze("MU")

    assert len(result.indicators) == 210
    assert result.indicators[-1].sma_200 is not None


def test_apply_explanation_keeps_engine_price_levels_unchanged() -> None:
    candidate = StrategyCandidate(
        template="long_breakout", direction=Direction.LONG, status=OpportunityStatus.VALID, score=80,
        entry=PriceRange(lower=99, center=100, upper=101, source="engine"),
        target_one=PriceRange(lower=110, center=111, upper=112, source="engine"),
        target_two=PriceRange(lower=120, center=121, upper=122, source="engine"), invalidation=95,
    )
    explanation = Explanation("结构确认", ["波动扩大"], ["收盘保持突破"], [100, 111])

    result = apply_explanation(candidate, explanation)

    assert result.reason == "结构确认"
    assert result.entry == candidate.entry
    assert result.invalidation == 95

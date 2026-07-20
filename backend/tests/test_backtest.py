from datetime import date

import pytest

from app.domain.models import Direction, OpportunityStatus, PriceRange, StrategyCandidate
from app.services.backtest import SAMPLE_OUT_OF_SAMPLE, SAMPLE_RESEARCH, assert_isolated_research_window, evaluate_candidate


def test_optimizer_window_cannot_include_out_of_sample_dates() -> None:
    assert_isolated_research_window(date(2023, 1, 1), date(2025, 12, 31))
    with pytest.raises(ValueError, match="2026"):
        assert_isolated_research_window(date(2023, 1, 1), SAMPLE_OUT_OF_SAMPLE.end)


def test_fixed_windows_match_the_confirmed_protocol() -> None:
    assert SAMPLE_RESEARCH.start == date(2023, 1, 1)
    assert SAMPLE_OUT_OF_SAMPLE.end == date(2026, 6, 30)


def test_candidate_backtest_marks_first_target_hit() -> None:
    candidate = StrategyCandidate(template="long_breakout", direction=Direction.LONG, status=OpportunityStatus.VALID, score=80, entry=PriceRange(lower=99, center=100, upper=101, source="engine"), target_one=PriceRange(lower=109, center=110, upper=111, source="engine"), target_two=PriceRange(lower=119, center=120, upper=121, source="engine"), invalidation=95)

    outcome = evaluate_candidate(candidate, [{"high": 111.0, "low": 99.0}])

    assert outcome == 0.10

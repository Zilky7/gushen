from datetime import date

import pytest

from app.services.backtest import SAMPLE_OUT_OF_SAMPLE, SAMPLE_RESEARCH, assert_isolated_research_window


def test_optimizer_window_cannot_include_out_of_sample_dates() -> None:
    assert_isolated_research_window(date(2023, 1, 1), date(2025, 12, 31))
    with pytest.raises(ValueError, match="2026"):
        assert_isolated_research_window(date(2023, 1, 1), SAMPLE_OUT_OF_SAMPLE.end)


def test_fixed_windows_match_the_confirmed_protocol() -> None:
    assert SAMPLE_RESEARCH.start == date(2023, 1, 1)
    assert SAMPLE_OUT_OF_SAMPLE.end == date(2026, 6, 30)

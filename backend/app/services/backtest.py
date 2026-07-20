from __future__ import annotations

from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class SampleWindow:
    start: date
    end: date


SAMPLE_RESEARCH = SampleWindow(date(2023, 1, 1), date(2025, 12, 31))
SAMPLE_OUT_OF_SAMPLE = SampleWindow(date(2026, 1, 1), date(2026, 6, 30))


def assert_isolated_research_window(start: date, end: date) -> None:
    if start < SAMPLE_RESEARCH.start or end > SAMPLE_RESEARCH.end:
        raise ValueError("Research/LLM optimization may only access 2023-01-01 through 2025-12-31, never 2026.")


@dataclass(frozen=True)
class BacktestMetrics:
    total_return: float
    win_rate: float
    max_drawdown: float
    average_payoff: float
    trade_count: int
    target_hit_rate: float
    invalidation_rate: float


def metrics_from_outcomes(outcomes: list[float], target_hits: int, invalidations: int) -> BacktestMetrics:
    count = len(outcomes)
    if not count:
        return BacktestMetrics(0, 0, 0, 0, 0, 0, 0)
    equity = 1.0
    peak = 1.0
    max_drawdown = 0.0
    for result in outcomes:
        equity *= 1 + result
        peak = max(peak, equity)
        max_drawdown = min(max_drawdown, equity / peak - 1)
    return BacktestMetrics(
        total_return=equity - 1,
        win_rate=sum(result > 0 for result in outcomes) / count,
        max_drawdown=max_drawdown,
        average_payoff=sum(outcomes) / count,
        trade_count=count,
        target_hit_rate=target_hits / count,
        invalidation_rate=invalidations / count,
    )

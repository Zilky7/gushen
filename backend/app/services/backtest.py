from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Iterable, Mapping

import pandas as pd

from app.domain.models import Direction, OhlcvBar, OpportunityStatus, StrategyCandidate
from app.engine.defaults import DEFAULT_PARAMETERS, StrategyParameters
from app.engine.indicators import compute_indicators
from app.engine.strategy import generate_candidates
from app.engine.zones import build_price_zones, find_pivots


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


def evaluate_candidate(candidate: StrategyCandidate, future_bars: Iterable[Mapping[str, float]]) -> float:
    """Return the first deterministic target/invalidation result as a fraction of entry price.

    A bar touching both levels is treated conservatively as invalidation first because intraday order is unknowable from daily OHLCV.
    """
    if candidate.status != OpportunityStatus.VALID or not all(
        (candidate.entry, candidate.target_one, candidate.invalidation is not None)
    ):
        raise ValueError("Only valid candidates with complete engine levels can be evaluated.")
    entry = candidate.entry.center
    target = candidate.target_one.center
    invalidation = candidate.invalidation
    for bar in future_bars:
        high, low = float(bar["high"]), float(bar["low"])
        if candidate.direction == Direction.LONG:
            if low <= invalidation:
                return (invalidation - entry) / entry
            if high >= target:
                return (target - entry) / entry
        else:
            if high >= invalidation:
                return (entry - invalidation) / entry
            if low <= target:
                return (entry - target) / entry
    return 0.0


def run_daily_backtest(bars: list[OhlcvBar], parameters: StrategyParameters = DEFAULT_PARAMETERS) -> BacktestMetrics:
    """Walk forward through daily bars without allowing a decision to see future candles."""
    if len(bars) <= parameters.sma_slow:
        return metrics_from_outcomes([], 0, 0)
    outcomes: list[float] = []
    target_hits = 0
    invalidations = 0
    index = parameters.sma_slow
    while index < len(bars) - 1:
        visible = bars[: index + 1]
        frame = pd.DataFrame([bar.model_dump() for bar in visible]).set_index("date").rename(
            columns={"open": "Open", "high": "High", "low": "Low", "close": "Close", "volume": "Volume"}
        )
        enriched = compute_indicators(frame, parameters)
        atr = enriched.iloc[-1].atr_14
        if pd.isna(atr):
            index += 1
            continue
        pivots = find_pivots([{"date": bar.date, "high": bar.high, "low": bar.low} for bar in visible], parameters.pivot_width)
        zones = build_price_zones(pivots, float(atr), visible[-1].close, visible[-1].date, parameters)
        candidates = [item for item in generate_candidates(frame, zones, parameters) if item.status == OpportunityStatus.VALID]
        if not candidates:
            index += 1
            continue
        candidate = max(candidates, key=lambda item: item.score)
        outcome = evaluate_candidate(candidate, [{"high": bar.high, "low": bar.low} for bar in bars[index + 1 : index + 11]])
        outcomes.append(outcome)
        if outcome > 0:
            target_hits += 1
        elif outcome < 0:
            invalidations += 1
        index += 10
    return metrics_from_outcomes(outcomes, target_hits, invalidations)

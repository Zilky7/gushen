from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class StrategyParameters:
    sma_fast: int = 20
    sma_mid: int = 50
    sma_slow: int = 200
    atr_period: int = 14
    volume_period: int = 20
    pivot_width: int = 3
    zone_atr_multiple: float = 0.8
    zone_percent: float = 0.01
    breakout_atr_multiple: float = 0.1
    volume_multiple: float = 1.2
    invalidation_atr_multiple: float = 1.0
    target_one_r: float = 1.5
    target_two_r: float = 2.5
    trend_weight: float = 35.0
    zone_weight: float = 30.0
    confirmation_weight: float = 20.0
    reward_weight: float = 15.0


DEFAULT_PARAMETERS = StrategyParameters()
STRATEGY_VERSION = "baseline-2026-07-20"

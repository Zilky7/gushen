from __future__ import annotations

import math

import pandas as pd

from app.domain.models import Direction, OpportunityStatus, PriceRange, PriceZone, StrategyCandidate
from app.engine.defaults import DEFAULT_PARAMETERS, StrategyParameters
from app.engine.indicators import compute_indicators


def _range(center: float, atr: float, source: str) -> PriceRange:
    half_width = max(atr * 0.15, center * 0.001)
    return PriceRange(lower=center - half_width, center=center, upper=center + half_width, source=source)


def _nearest(zones: list[PriceZone], kind: str, price: float, above: bool) -> PriceZone | None:
    candidates = [zone for zone in zones if zone.kind == kind and (zone.lower > price if above else zone.upper < price)]
    return min(candidates, key=lambda item: item.lower if above else -item.upper, default=None)


def _candidate(
    template: str,
    direction: Direction,
    entry_center: float,
    invalidation: float,
    target_one: float,
    target_two: float,
    atr: float,
    trend_confirmed: bool,
    zone_strength: float,
    signal_confirmed: bool,
    conditions: list[str],
    parameters: StrategyParameters,
) -> StrategyCandidate:
    risk = abs(entry_center - invalidation)
    reward = abs(target_one - entry_center)
    rr = reward / risk if risk else 0.0
    status = OpportunityStatus.VALID if rr >= 1.5 else OpportunityStatus.NO_OPPORTUNITY
    reward_component = min(1.0, rr / 2.5)
    score = (
        parameters.trend_weight * float(trend_confirmed)
        + parameters.zone_weight * min(1.0, zone_strength / 100)
        + parameters.confirmation_weight * float(signal_confirmed)
        + parameters.reward_weight * reward_component
    )
    return StrategyCandidate(
        template=template,
        direction=direction,
        status=status,
        score=round(min(100.0, max(0.0, score)), 1),
        entry=_range(entry_center, atr, "support/resistance zone"),
        target_one=_range(target_one, atr, "next key level"),
        target_two=_range(target_two, atr, "next key level"),
        invalidation=round(invalidation, 4),
        risk_reward_one=round(rr, 2),
        conditions=conditions,
        facts={
            "entry_center": entry_center,
            "atr_14": atr,
            "risk_reward_one": round(rr, 2),
            "trend_score": parameters.trend_weight * float(trend_confirmed),
            "zone_score": parameters.zone_weight * min(1.0, zone_strength / 100),
            "confirmation_score": parameters.confirmation_weight * float(signal_confirmed),
            "reward_score": parameters.reward_weight * reward_component,
        },
    )


def generate_candidates(
    frame: pd.DataFrame,
    zones: list[PriceZone],
    parameters: StrategyParameters = DEFAULT_PARAMETERS,
) -> list[StrategyCandidate]:
    enriched = compute_indicators(frame, parameters)
    latest = enriched.iloc[-1]
    required = ["atr_14", "sma_20", "sma_50", "sma_200", "sma_50_slope_10", "volume_sma_20"]
    if any(math.isnan(float(latest[name])) for name in required):
        return []
    close, atr = float(latest["Close"]), float(latest["atr_14"])
    long_trend = close > latest.sma_50 and latest.sma_20 > latest.sma_50 and latest.sma_50_slope_10 > 0
    short_trend = close < latest.sma_50 and latest.sma_20 < latest.sma_50 and latest.sma_50_slope_10 < 0
    volume_confirmed = latest.Volume >= latest.volume_sma_20 * parameters.volume_multiple
    bullish_reclaim = latest.Close > latest.Open and latest.Close > enriched.iloc[-2].Close
    bearish_rejection = latest.Close < latest.Open and latest.Close < enriched.iloc[-2].Close
    support = _nearest(zones, "support", close, above=False)
    resistance = _nearest(zones, "resistance", close, above=True)
    below_resistance = max((zone for zone in zones if zone.kind == "resistance" and zone.upper < close), key=lambda item: item.upper, default=None)
    above_support = min((zone for zone in zones if zone.kind == "support" and zone.lower > close), key=lambda item: item.lower, default=None)
    candidates: list[StrategyCandidate] = []

    if support and long_trend and bullish_reclaim and close <= support.upper + atr * 0.3 and close >= support.lower:
        entry = (support.lower + support.upper) / 2
        invalidation = support.lower - atr * parameters.invalidation_atr_multiple
        first = resistance.lower if resistance else entry + (entry - invalidation) * parameters.target_one_r
        second_zone = _nearest(zones, "resistance", first, above=True)
        second = second_zone.lower if second_zone else entry + (entry - invalidation) * parameters.target_two_r
        candidates.append(_candidate("long_pullback", Direction.LONG, entry, invalidation, first, second, atr, long_trend, support.strength, bullish_reclaim, ["uptrend", "support pullback", "bullish reclaim"], parameters))
    if below_resistance and long_trend and close >= below_resistance.upper + atr * parameters.breakout_atr_multiple and volume_confirmed:
        entry = close
        invalidation = below_resistance.lower - atr * parameters.invalidation_atr_multiple
        first = resistance.lower if resistance else entry + (entry - invalidation) * parameters.target_one_r
        second_zone = _nearest(zones, "resistance", first, above=True)
        second = second_zone.lower if second_zone else entry + (entry - invalidation) * parameters.target_two_r
        candidates.append(_candidate("long_breakout", Direction.LONG, entry, invalidation, first, second, atr, long_trend, below_resistance.strength, volume_confirmed, ["uptrend", "close above resistance", "volume confirmation"], parameters))
    if resistance and short_trend and bearish_rejection and close >= resistance.lower and close <= resistance.upper + atr * 0.3:
        entry = (resistance.lower + resistance.upper) / 2
        invalidation = resistance.upper + atr * parameters.invalidation_atr_multiple
        first = support.upper if support else entry - (invalidation - entry) * parameters.target_one_r
        second_zone = _nearest(zones, "support", first, above=False)
        second = second_zone.upper if second_zone else entry - (invalidation - entry) * parameters.target_two_r
        candidates.append(_candidate("short_rejection", Direction.SHORT, entry, invalidation, first, second, atr, short_trend, resistance.strength, bearish_rejection, ["downtrend", "resistance rejection", "bearish rejection"], parameters))
    if above_support and short_trend and close <= above_support.lower - atr * parameters.breakout_atr_multiple and volume_confirmed:
        entry = close
        invalidation = above_support.upper + atr * parameters.invalidation_atr_multiple
        first = support.upper if support else entry - (invalidation - entry) * parameters.target_one_r
        second_zone = _nearest(zones, "support", first, above=False)
        second = second_zone.upper if second_zone else entry - (invalidation - entry) * parameters.target_two_r
        candidates.append(_candidate("short_breakdown", Direction.SHORT, entry, invalidation, first, second, atr, short_trend, above_support.strength, volume_confirmed, ["downtrend", "close below support", "volume confirmation"], parameters))
    return candidates

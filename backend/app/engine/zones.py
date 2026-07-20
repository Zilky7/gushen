from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Iterable

from app.domain.models import PriceZone
from app.engine.defaults import DEFAULT_PARAMETERS, StrategyParameters


@dataclass(frozen=True)
class Pivot:
    kind: str
    price: float
    date: date


def _value(bar: object, name: str) -> float | date:
    if isinstance(bar, dict):
        return bar[name]
    return getattr(bar, name)


def find_pivots(bars: Iterable[object], width: int = 3) -> list[Pivot]:
    values = list(bars)
    pivots: list[Pivot] = []
    for index in range(width, len(values) - width):
        window = values[index - width : index + width + 1]
        high = float(_value(values[index], "high"))
        low = float(_value(values[index], "low"))
        surrounding = window[:width] + window[width + 1 :]
        pivot_date = _value(values[index], "date")
        if all(high > float(_value(item, "high")) for item in surrounding):
            pivots.append(Pivot("resistance", high, pivot_date))
        if all(low < float(_value(item, "low")) for item in surrounding):
            pivots.append(Pivot("support", low, pivot_date))
    return pivots


def build_price_zones(
    pivots: Iterable[Pivot],
    atr: float,
    close: float,
    as_of: date,
    parameters: StrategyParameters = DEFAULT_PARAMETERS,
) -> list[PriceZone]:
    """Cluster same-direction pivots using the current, explicitly supplied tolerance."""
    tolerance = max(parameters.zone_atr_multiple * atr, close * parameters.zone_percent)
    grouped: list[list[Pivot]] = []
    for pivot in sorted(pivots, key=lambda item: (item.kind, item.price, item.date)):
        if grouped and grouped[-1][0].kind == pivot.kind and pivot.price - grouped[-1][-1].price <= tolerance:
            grouped[-1].append(pivot)
        else:
            grouped.append([pivot])

    zones: list[PriceZone] = []
    for group in grouped:
        latest = max(item.date for item in group)
        age_days = max((as_of - latest).days, 0)
        recency = max(0.0, 30.0 - min(age_days, 30))
        strength = min(100.0, len(group) * 20.0 + recency)
        zones.append(
            PriceZone(
                kind=group[0].kind,
                lower=min(item.price for item in group),
                upper=max(item.price for item in group),
                strength=strength,
                touches=len(group),
                pivot_dates=sorted(item.date for item in group),
            )
        )
    return sorted(zones, key=lambda item: (item.kind, item.lower, item.upper))

import pandas as pd

from app.domain.models import Direction, PriceZone
from app.engine.strategy import generate_candidates


def test_long_breakout_has_atr_invalidation_and_fallback_targets() -> None:
    index = pd.date_range("2025-01-01", periods=210, freq="B")
    close = [100.0 + index_number * 0.1 for index_number in range(209)] + [125.0]
    frame = pd.DataFrame(
        {
            "Open": close,
            "High": [price + 1 for price in close],
            "Low": [price - 1 for price in close],
            "Close": close,
            "Volume": [100.0] * 209 + [200.0],
        },
        index=index,
    )
    zones = [
        PriceZone(kind="resistance", lower=120, upper=123, strength=80, touches=3, pivot_dates=[]),
        PriceZone(kind="support", lower=118, upper=120, strength=80, touches=3, pivot_dates=[]),
    ]

    candidates = generate_candidates(frame, zones)
    breakout = next(item for item in candidates if item.template == "long_breakout")

    assert breakout.direction == Direction.LONG
    assert breakout.invalidation is not None
    assert breakout.entry is not None
    assert breakout.target_one is not None
    assert breakout.target_two is not None
    assert breakout.target_one.center > breakout.entry.center
    assert breakout.score > 0


def test_pullback_requires_a_bullish_reclaiming_close() -> None:
    index = pd.date_range("2025-01-01", periods=210, freq="B")
    close = [100.0 + step * 0.1 for step in range(208)] + [121.0, 120.0]
    frame = pd.DataFrame({"Open": close, "High": [price + 1 for price in close], "Low": [price - 1 for price in close], "Close": close, "Volume": [1000.0] * 210}, index=index)
    zones = [PriceZone(kind="support", lower=119, upper=119.9, strength=80, touches=3, pivot_dates=[])]

    candidates = generate_candidates(frame, zones)

    assert all(item.template != "long_pullback" for item in candidates)

from datetime import date, timedelta

from app.engine.zones import build_price_zones, find_pivots


def test_finds_pivots_with_three_bars_on_each_side() -> None:
    values = [10, 11, 12, 13, 15, 13, 12, 11, 10, 11, 12, 13, 14]
    bars = [
        {"date": date(2026, 1, 1) + timedelta(days=index), "high": value, "low": value - 2}
        for index, value in enumerate(values)
    ]

    pivots = find_pivots(bars)

    assert [(pivot.kind, pivot.price) for pivot in pivots] == [("resistance", 15), ("support", 8)]


def test_groups_nearby_pivots_into_one_price_zone() -> None:
    bars = [
        {"date": date(2026, 1, 1), "high": 100, "low": 99},
        {"date": date(2026, 2, 1), "high": 100.5, "low": 99.5},
    ]
    pivots = [
        type("Pivot", (), {"kind": "resistance", "price": 100.0, "date": bars[0]["date"]})(),
        type("Pivot", (), {"kind": "resistance", "price": 100.5, "date": bars[1]["date"]})(),
    ]

    zones = build_price_zones(pivots, atr=1.0, close=100.0, as_of=date(2026, 2, 1))

    assert len(zones) == 1
    assert zones[0].lower == 100.0
    assert zones[0].upper == 100.5
    assert zones[0].touches == 2

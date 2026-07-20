import pandas as pd
import pytest

from app.engine.indicators import compute_indicators


def test_compute_indicators_uses_wilder_atr_and_rolling_values() -> None:
    frame = pd.DataFrame(
        {
            "Open": [10.0] * 15,
            "High": [11.0] * 15,
            "Low": [9.0] * 15,
            "Close": [10.0] * 14 + [12.0],
            "Volume": [100.0] * 14 + [200.0],
        },
        index=pd.date_range("2026-01-01", periods=15, freq="B"),
    )

    result = compute_indicators(frame)

    assert result["sma_20"].isna().all()
    assert result["sma_50"].isna().all()
    assert result.iloc[-1]["atr_14"] == pytest.approx(2.0)
    assert result.iloc[-1]["volume_sma_20"] != result.iloc[-1]["volume_sma_20"]
    assert result.iloc[-1]["true_range"] == pytest.approx(2.0)

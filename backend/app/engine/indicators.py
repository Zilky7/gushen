from __future__ import annotations

import pandas as pd

from app.engine.defaults import DEFAULT_PARAMETERS, StrategyParameters


def compute_indicators(
    frame: pd.DataFrame, parameters: StrategyParameters = DEFAULT_PARAMETERS
) -> pd.DataFrame:
    """Return a copied OHLCV frame enriched with daily, non-lookahead features."""
    required = {"High", "Low", "Close", "Volume"}
    missing = required.difference(frame.columns)
    if missing:
        raise ValueError(f"Missing OHLCV columns: {', '.join(sorted(missing))}")

    result = frame.copy()
    previous_close = result["Close"].shift(1)
    result["true_range"] = pd.concat(
        [
            result["High"] - result["Low"],
            (result["High"] - previous_close).abs(),
            (result["Low"] - previous_close).abs(),
        ],
        axis=1,
    ).max(axis=1)
    result["atr_14"] = result["true_range"].ewm(
        alpha=1 / parameters.atr_period, adjust=False, min_periods=parameters.atr_period
    ).mean()
    result["sma_20"] = result["Close"].rolling(parameters.sma_fast).mean()
    result["sma_50"] = result["Close"].rolling(parameters.sma_mid).mean()
    result["sma_200"] = result["Close"].rolling(parameters.sma_slow).mean()
    result["sma_50_slope_10"] = result["sma_50"] - result["sma_50"].shift(10)
    result["volume_sma_20"] = result["Volume"].rolling(parameters.volume_period).mean()
    return result

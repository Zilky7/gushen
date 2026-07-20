from datetime import timedelta

import pandas as pd
import pytest

from app.db import Database
from app.repositories import MarketCacheRepository
from app.services.market_data import MarketDataError, MarketDataService


def test_market_data_uses_stale_cache_when_download_fails(tmp_path) -> None:
    cache = MarketCacheRepository(Database(tmp_path / "cache.sqlite3"))
    service = MarketDataService(
        cache,
        downloader=lambda _: (_ for _ in ()).throw(RuntimeError("offline")),
        freshness=timedelta(seconds=-1),
    )
    cache.save("MU", service.to_bars(pd.DataFrame({"Open": [1], "High": [2], "Low": [1], "Close": [2], "Volume": [3]}, index=pd.DatetimeIndex(["2026-01-01"]))), service.now())

    result = service.get_daily_bars("mu")

    assert result.symbol == "MU"
    assert result.stale_cache is True


def test_market_data_rejects_short_downloads(tmp_path) -> None:
    frame = pd.DataFrame({"Open": [1], "High": [2], "Low": [1], "Close": [2], "Volume": [3]}, index=pd.DatetimeIndex(["2026-01-01"]))
    service = MarketDataService(MarketCacheRepository(Database(tmp_path / "cache.sqlite3")), downloader=lambda _: frame)

    with pytest.raises(MarketDataError, match="insufficient_data"):
        service.get_daily_bars("MU", minimum_bars=2)

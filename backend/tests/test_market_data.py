from datetime import date, timedelta

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
    service = MarketDataService(MarketCacheRepository(Database(tmp_path / "cache.sqlite3")), downloader=lambda _: frame, nasdaq_downloader=lambda _: pd.DataFrame())

    with pytest.raises(MarketDataError, match="insufficient_data"):
        service.get_daily_bars("MU", minimum_bars=2)


def test_market_data_falls_back_to_cache_when_refresh_is_insufficient(tmp_path) -> None:
    cache = MarketCacheRepository(Database(tmp_path / "cache.sqlite3"))
    stale_service = MarketDataService(cache, freshness=timedelta(seconds=-1), downloader=lambda _: pd.DataFrame({"Open": [1], "High": [2], "Low": [1], "Close": [2], "Volume": [3]}, index=pd.DatetimeIndex(["2026-01-01"])))
    cache.save("MU", stale_service.to_bars(pd.DataFrame({"Open": [1, 2], "High": [2, 3], "Low": [1, 2], "Close": [2, 3], "Volume": [3, 4]}, index=pd.DatetimeIndex(["2025-01-01", "2025-01-02"]))), stale_service.now())

    result = stale_service.get_daily_bars("MU", minimum_bars=2)

    assert result.stale_cache is True
    assert len(result.bars) == 2


def test_history_download_uses_explicit_research_dates(tmp_path) -> None:
    calls = []
    service = MarketDataService(
        MarketCacheRepository(Database(tmp_path / "cache.sqlite3")),
        history_downloader=lambda symbol, start, end: calls.append((symbol, start, end)) or pd.DataFrame({"Open": [1], "High": [2], "Low": [1], "Close": [2], "Volume": [3]}, index=pd.DatetimeIndex(["2025-01-01"])),
    )

    service.get_history_bars("mu", date(2023, 1, 1), date(2025, 12, 31), minimum_bars=1)

    assert calls == [("MU", date(2023, 1, 1), date(2025, 12, 31))]


def test_empty_provider_response_is_reported_as_temporary_market_data_failure(tmp_path) -> None:
    service = MarketDataService(
        MarketCacheRepository(Database(tmp_path / "cache.sqlite3")),
        downloader=lambda _: pd.DataFrame(),
        nasdaq_downloader=lambda _: pd.DataFrame(),
    )

    with pytest.raises(MarketDataError) as error:
        service.get_daily_bars("MU", minimum_bars=2)

    assert error.value.code == "empty_data"


def test_market_data_uses_nasdaq_fallback_when_yahoo_is_empty(tmp_path) -> None:
    yahoo = lambda _: pd.DataFrame()
    nasdaq = lambda _: pd.DataFrame(
        {"Open": [1], "High": [2], "Low": [1], "Close": [2], "Volume": [3]},
        index=pd.DatetimeIndex(["2026-01-01"]),
    )
    service = MarketDataService(
        MarketCacheRepository(Database(tmp_path / "cache.sqlite3")), downloader=yahoo, nasdaq_downloader=nasdaq
    )

    result = service.get_daily_bars("MU", minimum_bars=1)

    assert result.source == "nasdaq"
    assert len(result.bars) == 1

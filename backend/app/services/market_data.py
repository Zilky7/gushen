from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from typing import TYPE_CHECKING, Callable

from app.domain.models import OhlcvBar
from app.repositories import MarketCacheRepository

if TYPE_CHECKING:
    import pandas as pd


class MarketDataError(Exception):
    def __init__(self, code: str, message: str) -> None:
        self.code = code
        super().__init__(message)


@dataclass(frozen=True)
class MarketDataResult:
    symbol: str
    bars: list[OhlcvBar]
    updated_at: datetime
    stale_cache: bool
    source: str = "yfinance"


class MarketDataService:
    def __init__(
        self,
        cache: MarketCacheRepository,
        downloader: Callable[[str], "pd.DataFrame"] | None = None,
        history_downloader: Callable[[str, date, date], "pd.DataFrame"] | None = None,
        freshness: timedelta = timedelta(hours=24),
    ) -> None:
        self.cache = cache
        self.downloader = downloader or self._download
        self.history_downloader = history_downloader or self._download_history
        self.freshness = freshness

    @staticmethod
    def now() -> datetime:
        return datetime.now(UTC)

    @staticmethod
    def normalize_symbol(symbol: str) -> str:
        normalized = symbol.strip().upper()
        if not normalized or not normalized.replace(".", "").replace("-", "").isalnum():
            raise MarketDataError("invalid_symbol", "Ticker must contain letters, numbers, dots, or dashes.")
        return normalized

    @staticmethod
    def _download(symbol: str) -> "pd.DataFrame":
        import yfinance as yf

        return yf.download(symbol, period="2y", interval="1d", auto_adjust=False, progress=False)

    @staticmethod
    def _download_history(symbol: str, start: date, end: date) -> "pd.DataFrame":
        import yfinance as yf

        return yf.download(symbol, start=start.isoformat(), end=(end + timedelta(days=1)).isoformat(), interval="1d", auto_adjust=False, progress=False)

    @staticmethod
    def to_bars(frame: "pd.DataFrame") -> list[OhlcvBar]:
        import pandas as pd

        if frame.empty:
            raise MarketDataError(
                "empty_data",
                "行情源暂时未返回数据（通常是 yfinance/Yahoo 限流）；请稍后重试。",
            )
        if isinstance(frame.columns, pd.MultiIndex):
            frame = frame.copy()
            frame.columns = frame.columns.get_level_values(0)
        required = ["Open", "High", "Low", "Close", "Volume"]
        if any(column not in frame.columns for column in required):
            raise MarketDataError("invalid_data", "Downloaded data has no complete OHLCV columns.")
        result: list[OhlcvBar] = []
        for timestamp, row in frame.dropna(subset=required).iterrows():
            result.append(
                OhlcvBar(
                    date=pd.Timestamp(timestamp).date(),
                    open=float(row["Open"]), high=float(row["High"]), low=float(row["Low"]),
                    close=float(row["Close"]), volume=float(row["Volume"]),
                )
            )
        return result

    def get_daily_bars(self, symbol: str, minimum_bars: int = 210) -> MarketDataResult:
        ticker = self.normalize_symbol(symbol)
        cached = self.cache.get(ticker)
        if cached and self.now() - cached[1] <= self.freshness:
            return MarketDataResult(ticker, cached[0], cached[1], stale_cache=False)
        try:
            bars = self.to_bars(self.downloader(ticker))
            if len(bars) < minimum_bars:
                raise MarketDataError(
                    "insufficient_data", f"insufficient_data: only {len(bars)} daily bars are available."
                )
            fetched_at = self.now()
            self.cache.save(ticker, bars, fetched_at)
            return MarketDataResult(ticker, bars, fetched_at, stale_cache=False)
        except MarketDataError:
            if cached:
                return MarketDataResult(ticker, cached[0], cached[1], stale_cache=True)
            raise
        except Exception as error:
            if cached:
                return MarketDataResult(ticker, cached[0], cached[1], stale_cache=True)
            raise MarketDataError("fetch_failed", "Could not fetch daily market data.") from error

    def get_history_bars(
        self, symbol: str, start: date, end: date, minimum_bars: int = 210
    ) -> list[OhlcvBar]:
        if start > end:
            raise MarketDataError("invalid_dates", "Start date must not be after end date.")
        ticker = self.normalize_symbol(symbol)
        try:
            bars = self.to_bars(self.history_downloader(ticker, start, end))
        except MarketDataError:
            raise
        except Exception as error:
            raise MarketDataError("fetch_failed", "Could not fetch historical daily market data.") from error
        if len(bars) < minimum_bars:
            raise MarketDataError("insufficient_data", f"insufficient_data: only {len(bars)} daily bars are available.")
        return bars

from __future__ import annotations

from datetime import datetime
import json

from app.db import Database
from app.domain.models import AnalysisResult, OhlcvBar


class AnalysisRepository:
    def __init__(self, database: Database) -> None:
        self.database = database

    def save_analysis(self, analysis: AnalysisResult) -> None:
        with self.database.connect() as connection:
            connection.execute(
                "INSERT INTO analyses (id, symbol, created_at, payload) VALUES (?, ?, ?, ?)",
                (analysis.id, analysis.symbol, analysis.created_at.isoformat(), analysis.model_dump_json()),
            )

    def get_analysis(self, analysis_id: str) -> AnalysisResult | None:
        with self.database.connect() as connection:
            row = connection.execute("SELECT payload FROM analyses WHERE id = ?", (analysis_id,)).fetchone()
        return AnalysisResult.model_validate_json(row["payload"]) if row else None

    def list_analyses(self, limit: int = 30) -> list[AnalysisResult]:
        with self.database.connect() as connection:
            rows = connection.execute(
                "SELECT payload FROM analyses ORDER BY created_at DESC LIMIT ?", (limit,)
            ).fetchall()
        return [AnalysisResult.model_validate_json(row["payload"]) for row in rows]


class MarketCacheRepository:
    def __init__(self, database: Database) -> None:
        self.database = database

    def save(self, symbol: str, bars: list[OhlcvBar], fetched_at: datetime, source: str = "yfinance") -> None:
        payload = json.dumps([bar.model_dump(mode="json") for bar in bars])
        with self.database.connect() as connection:
            connection.execute(
                "INSERT OR REPLACE INTO market_cache (symbol, fetched_at, source, payload) VALUES (?, ?, ?, ?)",
                (symbol, fetched_at.isoformat(), source, payload),
            )

    def get(self, symbol: str) -> tuple[list[OhlcvBar], datetime, str] | None:
        with self.database.connect() as connection:
            row = connection.execute(
                "SELECT fetched_at, source, payload FROM market_cache WHERE symbol = ?", (symbol,)
            ).fetchone()
        if not row:
            return None
        return ([OhlcvBar.model_validate(item) for item in json.loads(row["payload"])], datetime.fromisoformat(row["fetched_at"]), row["source"])

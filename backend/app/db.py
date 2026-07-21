from __future__ import annotations

import sqlite3
from pathlib import Path


class Database:
    def __init__(self, path: str | Path = "data/gushen.sqlite3") -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.initialize()

    def connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        return connection

    def initialize(self) -> None:
        with self.connect() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS analyses (
                    id TEXT PRIMARY KEY,
                    symbol TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    payload TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS market_cache (
                    symbol TEXT PRIMARY KEY,
                    fetched_at TEXT NOT NULL,
                    source TEXT NOT NULL DEFAULT 'yfinance',
                    payload TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS strategy_versions (
                    id TEXT PRIMARY KEY,
                    created_at TEXT NOT NULL,
                    parent_id TEXT,
                    parameters TEXT NOT NULL,
                    rationale TEXT NOT NULL,
                    metrics TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS backtest_reports (
                    id TEXT PRIMARY KEY,
                    created_at TEXT NOT NULL,
                    strategy_version TEXT NOT NULL,
                    sample_start TEXT NOT NULL,
                    sample_end TEXT NOT NULL,
                    payload TEXT NOT NULL
                );
                """
            )
            columns = {row["name"] for row in connection.execute("PRAGMA table_info(market_cache)")}
            if "source" not in columns:
                connection.execute("ALTER TABLE market_cache ADD COLUMN source TEXT NOT NULL DEFAULT 'yfinance'")

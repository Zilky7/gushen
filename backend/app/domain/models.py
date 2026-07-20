from __future__ import annotations

from datetime import date, datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class Direction(StrEnum):
    LONG = "long"
    SHORT = "short"


class OpportunityStatus(StrEnum):
    VALID = "valid"
    NO_OPPORTUNITY = "no_opportunity"


class OhlcvBar(BaseModel):
    model_config = ConfigDict(frozen=True)

    date: date
    open: float = Field(gt=0)
    high: float = Field(gt=0)
    low: float = Field(gt=0)
    close: float = Field(gt=0)
    volume: float = Field(ge=0)


class PriceZone(BaseModel):
    model_config = ConfigDict(frozen=True)

    kind: str
    lower: float = Field(gt=0)
    upper: float = Field(gt=0)
    strength: float = Field(ge=0, le=100)
    touches: int = Field(ge=1)
    pivot_dates: list[date]


class IndicatorPoint(BaseModel):
    model_config = ConfigDict(frozen=True)

    date: date
    sma_20: float | None = None
    sma_50: float | None = None
    sma_200: float | None = None


class PriceRange(BaseModel):
    model_config = ConfigDict(frozen=True)

    lower: float = Field(gt=0)
    center: float = Field(gt=0)
    upper: float = Field(gt=0)
    source: str


class StrategyCandidate(BaseModel):
    model_config = ConfigDict(frozen=True)

    template: str
    direction: Direction
    status: OpportunityStatus
    score: float = Field(ge=0, le=100)
    entry: PriceRange | None = None
    target_one: PriceRange | None = None
    target_two: PriceRange | None = None
    invalidation: float | None = Field(default=None, gt=0)
    risk_reward_one: float | None = Field(default=None, ge=0)
    conditions: list[str] = Field(default_factory=list)
    facts: dict[str, float | str | bool] = Field(default_factory=dict)
    reason: str | None = None
    risks: list[str] = Field(default_factory=list)
    triggers: list[str] = Field(default_factory=list)


class AnalysisResult(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: str
    symbol: str
    created_at: datetime
    data_updated_at: datetime
    data_source: str = "yfinance"
    stale_cache: bool = False
    strategy_version: str
    bars: list[OhlcvBar]
    indicators: list[IndicatorPoint] = Field(default_factory=list)
    zones: list[PriceZone]
    candidates: list[StrategyCandidate]

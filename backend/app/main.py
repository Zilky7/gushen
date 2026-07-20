from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.db import Database
from app.repositories import AnalysisRepository, MarketCacheRepository
from app.services.analysis import AnalysisService
from app.services.market_data import MarketDataError, MarketDataService
from app.services.research import ResearchService


def create_app(database_path: str | Path = "data/gushen.sqlite3") -> FastAPI:
    app = FastAPI(title="Gushen Strategy Research API", version="0.1.0")
    app.state.database = Database(database_path)
    app.state.analysis_repository = AnalysisRepository(app.state.database)
    app.state.analysis_service = AnalysisService(
        MarketDataService(MarketCacheRepository(app.state.database)), app.state.analysis_repository
    )
    app.state.research_service = ResearchService(app.state.analysis_service.market_data)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173"],
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/api/health")
    def health() -> dict[str, str | bool]:
        return {"service": "gushen", "execution_enabled": False, "disclaimer": "research only"}

    @app.post("/api/analysis")
    def create_analysis(symbol: str) -> dict:
        try:
            return app.state.analysis_service.analyze(symbol).model_dump(mode="json")
        except MarketDataError as error:
            raise HTTPException(status_code=422, detail={"code": error.code, "message": str(error)}) from error

    @app.get("/api/analyses")
    def list_analyses() -> list[dict]:
        return [analysis.model_dump(mode="json") for analysis in app.state.analysis_repository.list_analyses()]

    @app.get("/api/analyses/{analysis_id}")
    def get_analysis(analysis_id: str) -> dict:
        result = app.state.analysis_repository.get_analysis(analysis_id)
        if result is None:
            raise HTTPException(status_code=404, detail="Analysis record not found")
        return result.model_dump(mode="json")

    @app.post("/api/research/baseline")
    def create_baseline_research(symbol: str) -> dict:
        try:
            return app.state.research_service.baseline_report(symbol)
        except MarketDataError as error:
            raise HTTPException(status_code=422, detail={"code": error.code, "message": str(error)}) from error

    return app


app = create_app()

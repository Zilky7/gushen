from datetime import date, datetime, timezone

from app.db import Database
from app.domain.models import AnalysisResult, OhlcvBar
from app.repositories import AnalysisRepository


def test_analysis_repository_round_trips_an_immutable_analysis(tmp_path) -> None:
    repository = AnalysisRepository(Database(tmp_path / "gushen.sqlite3"))
    result = AnalysisResult(
        id="analysis-1",
        symbol="MU",
        created_at=datetime(2026, 7, 20, tzinfo=timezone.utc),
        data_updated_at=datetime(2026, 7, 20, tzinfo=timezone.utc),
        strategy_version="baseline",
        bars=[OhlcvBar(date=date(2026, 7, 20), open=1, high=2, low=1, close=2, volume=3)],
        zones=[],
        candidates=[],
    )

    repository.save_analysis(result)

    assert repository.get_analysis("analysis-1") == result
    assert repository.list_analyses()[0].symbol == "MU"

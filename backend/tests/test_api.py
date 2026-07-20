from fastapi.testclient import TestClient

from app.main import create_app


def test_health_endpoint_describes_research_only_service(tmp_path) -> None:
    app = create_app(database_path=tmp_path / "test.sqlite3")

    response = TestClient(app).get("/api/health")

    assert response.status_code == 200
    assert response.json()["service"] == "gushen"
    assert response.json()["execution_enabled"] is False

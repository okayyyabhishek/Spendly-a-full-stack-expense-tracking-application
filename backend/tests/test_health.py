from fastapi.testclient import TestClient

from app.main import app


def test_health_check_is_available_without_authentication() -> None:
    response = TestClient(app).get("/api/v1/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "expense-tracker-api",
        "version": "0.1.0",
    }

from fastapi.testclient import TestClient

from polytrader.api.app import app


def test_data_health_endpoint_is_read_only_and_explicit() -> None:
    response = TestClient(app).get("/api/v1/data-health")
    assert response.status_code == 200
    assert response.json()["status"] in {"FRESH", "STALE", "DISCONNECTED", "INVALID"}
    assert response.json()["can_open_exposure"] is False

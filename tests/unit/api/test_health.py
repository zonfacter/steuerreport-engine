from fastapi.testclient import TestClient

from tax_engine.api import app


def test_health_endpoint_returns_standard_response() -> None:
    client = TestClient(app)
    response = client.get("/api/v1/health")

    assert response.status_code == 200
    payload = response.json()

    assert payload["status"] == "success"
    assert isinstance(payload["trace_id"], str)
    assert isinstance(payload["data"], dict)
    assert payload["data"]["service"] == "steuerreport-engine"
    assert payload["data"]["uptime_state"] == "ok"
    assert isinstance(payload["errors"], list)
    assert isinstance(payload["warnings"], list)

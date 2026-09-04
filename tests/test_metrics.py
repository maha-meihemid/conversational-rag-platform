from fastapi.testclient import TestClient

from app.main import app


def test_metrics_endpoint_exposes_http_metrics() -> None:
    client = TestClient(app)

    client.get("/api/v1/health")
    response = client.get("/metrics")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/plain")
    assert "rag_http_requests_total" in response.text
    assert 'method="GET"' in response.text
    assert 'route="/health"' in response.text
    assert 'status_code="200"' in response.text
    assert "rag_http_request_duration_seconds" in response.text

import json
import logging

from fastapi.testclient import TestClient

from app.core.logging import JsonFormatter
from app.main import app


def test_json_formatter_includes_request_fields() -> None:
    record = logging.LogRecord(
        name="app.requests",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg="Request completed",
        args=(),
        exc_info=None,
    )
    record.request_id = "request-123"
    record.method = "GET"
    record.path = "/api/v1/health"
    record.status_code = 200
    record.duration_ms = 1.25

    payload = json.loads(JsonFormatter().format(record))

    assert payload["message"] == "Request completed"
    assert payload["request_id"] == "request-123"
    assert payload["status_code"] == 200
    assert payload["duration_ms"] == 1.25


def test_response_contains_request_id() -> None:
    response = TestClient(app).get("/api/v1/health")

    assert response.status_code == 200
    assert response.headers["X-Request-ID"]

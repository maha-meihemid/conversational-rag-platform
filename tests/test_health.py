from fastapi.testclient import TestClient

from app.main import app
from app.services.readiness import run_readiness_checks

client = TestClient(app)


def test_health_check() -> None:
    response = client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "conversational-rag-platform",
    }


def test_readiness_check_returns_ready() -> None:
    app.dependency_overrides[run_readiness_checks] = lambda: {
        "configuration": "ok",
        "vector_store": "ok",
        "conversation_store": "ok",
    }

    response = client.get("/api/v1/ready")

    app.dependency_overrides.clear()
    assert response.status_code == 200
    assert response.json() == {
        "status": "ready",
        "checks": {
            "configuration": "ok",
            "vector_store": "ok",
            "conversation_store": "ok",
        },
    }


def test_readiness_check_returns_503_when_dependency_is_unavailable() -> None:
    app.dependency_overrides[run_readiness_checks] = lambda: {
        "configuration": "ok",
        "vector_store": "unavailable",
        "conversation_store": "ok",
    }

    response = client.get("/api/v1/ready")

    app.dependency_overrides.clear()
    assert response.status_code == 503
    assert response.json()["status"] == "unavailable"
    assert response.json()["checks"]["vector_store"] == "unavailable"

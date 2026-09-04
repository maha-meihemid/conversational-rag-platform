from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_web_app_is_served() -> None:
    response = client.get("/")

    assert response.status_code == 200
    assert "Conversational RAG Platform" in response.text
    assert 'id="chat-form"' in response.text
    assert 'id="api-key"' in response.text


def test_web_assets_are_served() -> None:
    css_response = client.get("/static/styles.css")
    js_response = client.get("/static/app.js")

    assert css_response.status_code == 200
    assert js_response.status_code == 200
    assert "--accent" in css_response.text
    assert 'const API_BASE = "/api/v1"' in js_response.text
    assert 'headers["X-API-Key"]' in js_response.text

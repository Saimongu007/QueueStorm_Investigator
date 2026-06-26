"""Test GET /health endpoint."""

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health_returns_ok():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"


def test_health_response_is_json():
    response = client.get("/health")
    assert response.headers["content-type"] == "application/json"

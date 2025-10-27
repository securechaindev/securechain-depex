"""Unit tests for health controller."""
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.controllers.health_controller import router


@pytest.fixture
def client():
    """Create a test client."""
    app = FastAPI()
    app.include_router(router)
    return TestClient(app)


class TestHealthController:
    """Test suite for health controller."""

    def test_health_check_success(self, client):
        """Test health check endpoint returns healthy status."""
        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert "detail" in data
        assert data["detail"] == "healthy"

    def test_health_check_response_structure(self, client):
        """Test health check response has correct structure."""
        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        assert len(data) == 1
        assert "detail" in data

    def test_health_check_content_type(self, client):
        """Test health check returns JSON content type."""
        response = client.get("/health")

        assert response.status_code == 200
        assert "application/json" in response.headers["content-type"]

    def test_health_check_multiple_requests(self, client):
        """Test multiple health check requests."""
        for _ in range(5):
            response = client.get("/health")
            assert response.status_code == 200
            assert response.json()["detail"] == "healthy"

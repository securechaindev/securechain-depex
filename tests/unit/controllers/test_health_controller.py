import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.controllers.health_controller import router


@pytest.fixture
def client():
    app = FastAPI()
    app.include_router(router)
    return TestClient(app)


class TestHealthController:
    def test_health_check_success(self, client):
        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert "detail" in data
        assert data["detail"] == "healthy"

    def test_health_check_response_structure(self, client):
        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        assert len(data) == 1
        assert "detail" in data

    def test_health_check_content_type(self, client):
        response = client.get("/health")

        assert response.status_code == 200
        assert "application/json" in response.headers["content-type"]

    def test_health_check_multiple_requests(self, client):
        for _ in range(5):
            response = client.get("/health")
            assert response.status_code == 200
            assert response.json()["detail"] == "healthy"

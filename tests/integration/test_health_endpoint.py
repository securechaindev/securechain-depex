from fastapi import status


class TestHealthEndpoint:

    def test_health_check_returns_ok(self, client):
        response = client.get("/health")
        assert response.status_code == status.HTTP_200_OK

    def test_health_check_response_structure(self, client):
        response = client.get("/health")
        data = response.json()
        assert "code" in data
        assert "message" in data
        assert data["code"] == "healthy"

    def test_health_check_with_full_app_context(self, client):
        response = client.get("/health")

        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert isinstance(data, dict)
        assert len(data) == 2

        assert data["code"] == "healthy"
        assert data["message"] == "The API is running and healthy."

        assert "application/json" in response.headers["content-type"]

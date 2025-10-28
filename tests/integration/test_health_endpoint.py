from fastapi import status


class TestHealthEndpoint:

    def test_health_check_returns_ok(self, client):
        response = client.get("/health")
        assert response.status_code == status.HTTP_200_OK

    def test_health_check_response_structure(self, client):
        response = client.get("/health")
        data = response.json()
        assert "detail" in data
        assert data["detail"] == "healthy"

    def test_health_check_with_full_app_context(self, client):
        response = client.get("/health")

        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert isinstance(data, dict)
        assert len(data) == 1

        assert data["detail"] == "healthy"

        assert "application/json" in response.headers["content-type"]

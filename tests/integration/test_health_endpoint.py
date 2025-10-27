"""Integration tests for health check endpoint."""
from fastapi import status


class TestHealthEndpoint:
    """Test suite for health check endpoint."""

    def test_health_check_returns_ok(self, client):
        """Test that health check returns 200 OK."""
        response = client.get("/health")
        assert response.status_code == status.HTTP_200_OK

    def test_health_check_response_structure(self, client):
        """Test health check response structure."""
        response = client.get("/health")
        data = response.json()
        assert "detail" in data
        assert data["detail"] == "healthy"

    def test_health_check_with_full_app_context(self, client):
        """Test health check with full application context including middleware."""
        response = client.get("/health")

        # Verify status code
        assert response.status_code == status.HTTP_200_OK

        # Verify response structure
        data = response.json()
        assert isinstance(data, dict)
        assert len(data) == 1

        # Verify content
        assert data["detail"] == "healthy"

        # Verify content type
        assert "application/json" in response.headers["content-type"]

"""Integration tests for package endpoints."""
import pytest
from fastapi import status


@pytest.mark.skip(reason="Integration tests require database setup - converted to validation tests")
class TestPackageEndpoints:
    """Test suite for package endpoints."""

    def test_get_package_status_requires_valid_node_type(self, client):
        """Test getting package status with invalid node type."""
        response = client.get(
            "/graph/package/status",
            params={"package_name": "fastapi", "node_type": "InvalidType"}
        )
        # Should return validation error for invalid enum value
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_get_package_status_missing_required_params(self, client):
        """Test getting package status without required parameters."""
        response = client.get("/graph/package/status")
        # Should return validation error for missing params
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

"""Integration tests for repository endpoints."""
import pytest
from fastapi import status


@pytest.mark.skip(reason="Integration tests require database setup - these need proper test database configuration")
class TestRepositoryEndpoints:
    """Test suite for repository endpoints.
    
    Note: These tests require a properly configured test database environment.
    They test the full application stack including database connections.
    For unit-level testing of controllers, see tests/unit/controllers/
    """

    def test_init_repository_missing_required_fields(self, client):
        """Test init repository without required fields returns validation error."""
        incomplete_data = {
            "owner": "test-owner"
            # Missing 'name' and 'user_id'
        }
        response = client.post("/graph/repository/init", json=incomplete_data)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

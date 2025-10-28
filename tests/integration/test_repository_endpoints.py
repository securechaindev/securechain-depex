import pytest
from fastapi import status


@pytest.mark.skip(reason="Integration tests require database setup - these need proper test database configuration")
class TestRepositoryEndpoints:
    def test_init_repository_missing_required_fields(self, client):
        incomplete_data = {
            "owner": "test-owner"
        }
        response = client.post("/graph/repository/init", json=incomplete_data)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

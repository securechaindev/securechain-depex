import pytest
from fastapi import status


@pytest.mark.skip(reason="Integration tests require database setup - converted to validation tests")
class TestPackageEndpoints:
    def test_get_package_status_requires_valid_node_type(self, client):
        response = client.get(
            "/graph/package/status",
            params={"package_name": "fastapi", "node_type": "InvalidType"}
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_get_package_status_missing_required_params(self, client):
        response = client.get("/graph/package/status")
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
